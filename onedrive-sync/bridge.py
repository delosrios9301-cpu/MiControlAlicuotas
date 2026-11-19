#!/usr/bin/env python3
"""OneDrive -> Firebase (solo espejos pendientes, sin modificar Excel ni confirmar congelación)."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import subprocess
from pathlib import PurePosixPath
from urllib.parse import quote
import openpyxl
import requests

SHEETS = {
    'ALMACENAMIENTO DE ALICUOTAS': ('B', 'X', ['study', 'sampleType', 'subject', 'visit', 'barcode', 'aliquotType', 'pivot', 'qty', 'freezer', 'drawer', 'box', 'position', 'operator', 'entryDate', 'note', 'cyclicCount', 'cyclicDate', 'cyclicOperator', 'cyclicNote', 'validation', 'validationDate', 'validationOperator', 'validationNote'], 'aliquot'),
    'SALIDA DE MUESTRA': ('A', 'M', ['study', 'sampleType', 'subject', 'visit', 'barcode', 'aliquotType', 'pivot', 'qty', 'trackingCode', 'exitDate', 'guide', 'operator', 'note'], 'exit'),
}
SESSION = requests.Session()
TIMEOUT = 35

def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)

def safe_cell(value):
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    return value

def row_data(sheet, values):
    schema = SHEETS[sheet]
    fields = schema[2]
    values = list(values)
    if len(values) != len(fields):
        raise ValueError('Columnas incompatibles con el esquema de ' + sheet)
    data = dict(zip(fields, map(safe_cell, values)))
    data['sheetKind'] = schema[3]
    if not any(str(data[k]).strip() for k in ('subject', 'barcode', 'study')):
        return None
    return data

def extract_rows(content):
    workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    try:
        if not set(SHEETS).intersection(workbook.sheetnames):
            raise ValueError('El Excel no contiene las hojas esperadas; no se importó ninguna fila.')
        result = []
        for sheet, (start, end, _, _) in SHEETS.items():
            if sheet not in workbook.sheetnames:
                continue
            sh = workbook[sheet]
            for number, row in enumerate(sh.iter_rows(min_row=4,
                        min_col=openpyxl.utils.column_index_from_string(start),
                        max_col=openpyxl.utils.column_index_from_string(end), values_only=True), start=4):
                if not row:
                    continue
                data = row_data(sheet, row)
                if data is not None:
                    result.append((sheet, number, data))
        return result
    finally:
        workbook.close()

def request(method, url, **opts):
    result = SESSION.request(method, url, timeout=TIMEOUT, **opts)
    if not result.ok:
        raise RuntimeError(f'Error HTTP {result.status_code} en servicio remoto; no se publicaron datos de este intento.')
    return result

def graph_access_token():
    form = {
        'client_id': os.environ['ONEDRIVE_CLIENT_ID'],
        'refresh_token': os.environ['ONEDRIVE_REFRESH_TOKEN'],
        'grant_type': 'refresh_token',
        'scope': 'offline_access Files.Read User.Read',
    }
    if os.environ.get('ONEDRIVE_CLIENT_SECRET'):
        form['client_secret'] = os.environ['ONEDRIVE_CLIENT_SECRET']
    response = request('POST', 'https://login.microsoftonline.com/common/oauth2/v2.0/token', data=form).json()
    return response['access_token']

def graph_file():
    token = graph_access_token()
    drive_id = quote(os.environ['ONEDRIVE_DRIVE_ID'], safe='')
    item_id = quote(os.environ['ONEDRIVE_ITEM_ID'], safe='')
    uri = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}'
    headers = {'Authorization': 'Bearer ' + token}
    info = request('GET', uri, headers=headers).json()
    if not str(info.get('name', '')).lower().endswith('.xlsx'):
        raise ValueError('El archivo seleccionado no es un .xlsx compatible.')
    raw = SESSION.get(uri + '/content', headers=headers, timeout=TIMEOUT, allow_redirects=False)
    if raw.status_code in (301, 302, 303, 307, 308):
        target = raw.headers.get('Location', '')
        if not target.startswith('https://'):
            raise ValueError('Redirección de descarga insegura.')
        content = request('GET', target).content
    elif raw.ok:
        content = raw.content
    else:
        raise RuntimeError(f'Descarga de Excel no disponible (HTTP {raw.status_code}).')
    if len(content) > 15_000_000:
        raise ValueError('Excel demasiado grande para el capturador gratuito (15 MB).')
    return info, content

def validated_rclone_path():
    path = os.environ.get('ONEDRIVE_RELATIVE_PATH', '').strip()
    if (not path or len(path) > 600 or not path.lower().endswith('.xlsx')
            or path.startswith(('/', chr(92))) or chr(92) in path or ':' in path
            or any(part in ('', '.', '..') for part in path.split('/'))):
        raise ValueError('Ruta de OneDrive no válida; selecciona un Excel .xlsx de tu copia personal.')
    return path

def rclone_file():
    # Rclone proporciona OAuth oficial por su aplicación compartida (sin registro propio Azure).
    # Solo el archivo seleccionado se descarga en memoria, sin registrarlo ni guardarlo en GitHub.
    relative_path = validated_rclone_path()
    if not os.environ.get('RCLONE_CONFIG_ONEDRIVE_TOKEN'):
        raise RuntimeError('Pendiente: autorizar OneDrive personal y guardar su token como secreto.')
    args = ['rclone', '--config', 'NUL' if os.name == 'nt' else '/dev/null',
            'cat', 'onedrive:' + relative_path]
    try:
        completed = subprocess.run(args, capture_output=True, timeout=150, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('OneDrive no respondió; no se transmitió ninguna fila.')
    if completed.returncode != 0:
        raise RuntimeError('No se pudo leer el Excel privado de OneDrive; verifica autorización y ruta.')
    content = completed.stdout
    if not content or len(content) > 15_000_000:
        raise ValueError('El Excel está vacío o supera los 15 MB permitidos para esta prueba.')
    return {'name': PurePosixPath(relative_path).name,
            'eTag': hashlib.sha256(content).hexdigest()}, content

def onedrive_file():
    mode = os.environ.get('ONEDRIVE_ACCESS_METHOD', 'graph').strip().lower()
    if mode == 'rclone':
        return rclone_file()
    if mode == 'graph':
        return graph_file()
    raise ValueError('Método de autorización de OneDrive no admitido.')

def source_reference():
    drive_id = os.environ['ONEDRIVE_DRIVE_ID']
    if os.environ.get('ONEDRIVE_ACCESS_METHOD', 'graph').strip().lower() == 'rclone':
        return drive_id, 'path:' + validated_rclone_path()
    return drive_id, os.environ['ONEDRIVE_ITEM_ID']

def firestore_base():
    project = os.environ['FIREBASE_PROJECT_ID']
    uid = os.environ['FIREBASE_OWNER_UID']
    if not re.fullmatch(r'[a-z][a-z0-9-]{3,40}', project) or not re.fullmatch(r'[A-Za-z0-9_-]{5,150}', uid):
        raise ValueError('Identificador de Firebase inválido.')
    return f'https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents/owners/{uid}'

def firestore(method, path, payload=None, missing_ok=False):
    headers = {'Authorization': 'Bearer ' + os.environ['GCP_ACCESS_TOKEN']}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    response = SESSION.request(method, path, headers=headers, json=payload, timeout=TIMEOUT)
    if response.status_code == 404 and missing_ok:
        return None
    if not response.ok:
        raise RuntimeError(f'Firestore rechazó una operación (HTTP {response.status_code}).')
    return response.json()

def source_id(drive_id, item_id, sheet, row):
    digest = hashlib.sha256(canon([drive_id, item_id, sheet, row]).encode()).hexdigest()
    return 'excel:onedrive:' + digest

def doc_url(base, rid):
    digest = hashlib.sha256(('mirrors\n' + rid).encode()).hexdigest()
    return base + '/entries/' + digest

def state_url(base, drive_id, item_id):
    code = hashlib.sha256(canon([drive_id, item_id]).encode()).hexdigest()
    return base + '/syncState/onedrive-' + code

def previous_data(doc):
    if not doc:
        return None, None
    fields = doc.get('fields', {})
    raw = fields.get('payload', {}).get('stringValue')
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return None, doc.get('updateTime')
    return obj, doc.get('updateTime')

def mirror_payload(rid, source_name, sheet, number, data, prior=None):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    return {
        'id': rid, 'sourceBook': source_name, 'sourceSheet': sheet,
        'sourceRow': number, 'sourceEventId': 0, 'timestamp': now,
        'data': data, 'importedAt': (prior or {}).get('importedAt'),
        'importedRecordId': (prior or {}).get('importedRecordId'),
        'dismissedAt': None,
        'reviewNote': 'El Excel cambió después de revisión.' if prior and prior.get('reviewedAt') else None,
        'reviewedAt': None, 'sourceOrigin': 'onedrive',
        'sourceLocalId': f'{sheet}|{number}',
    }

def put_mirror(base, rid, value, update_time=None):
    digest = hashlib.sha256(canon(value['data']).encode()).hexdigest()
    fields = {
        'table': {'stringValue': 'mirrors'}, 'recordId': {'stringValue': rid},
        'payload': {'stringValue': canon(value)}, 'revision': {'stringValue': digest},
        'deleted': {'booleanValue': False},
    }
    payload = {'writes': [{
        'update': {'name': doc_url(base, rid).replace('https://firestore.googleapis.com/v1/', ''), 'fields': fields},
        'updateTransforms': [{'fieldPath': 'syncedAt', 'setToServerValue': 'REQUEST_TIME'}],
        'currentDocument': {'updateTime': update_time} if update_time else {'exists': False},
    }]}
    project_root = base.split('/documents/')[0]
    firestore('POST', project_root + '/documents:commit', payload)

def write_state(url, etag):
    firestore('PATCH', url, {'fields': {
        'etag': {'stringValue': etag},
        'checkedAt': {'timestampValue': dt.datetime.now(dt.timezone.utc).isoformat()},
    }})

def sync(dry_run=True):
    info, content = onedrive_file()
    rows = extract_rows(content)
    print('Excel reconocido: hojas compatibles, filas no vacías:', len(rows))
    if dry_run:
        print('Modo prueba: no se publicó ningún dato ni se modificó el Excel.')
        return len(rows), 0
    base = firestore_base()
    drive_id, item_id = source_reference()
    state = state_url(base, drive_id, item_id)
    old = firestore('GET', state, missing_ok=True)
    etag = info.get('eTag') or hashlib.sha256(content).hexdigest()
    if old and old.get('fields', {}).get('etag', {}).get('stringValue') == etag:
        print('Sin cambios en el Excel; no se escribieron documentos.')
        return len(rows), 0
    changed = 0
    for sheet, number, data in rows:
        rid = source_id(drive_id, item_id, sheet, number)
        before = firestore('GET', doc_url(base, rid), missing_ok=True)
        previous, timestamp = previous_data(before)
        if previous and previous.get('data') == data:
            continue
        entry = mirror_payload(rid, info['name'], sheet, number, data, previous)
        if len(canon(entry).encode()) > 890000:
            raise ValueError('Fila demasiado grande; no se actualizó el estado de sincronización.')
        put_mirror(base, rid, entry, timestamp)
        changed += 1
    write_state(state, etag)
    print('Espejos actualizados:', changed, '(sin confirmar congelaciones)')
    return len(rows), changed

def main():
    p = argparse.ArgumentParser(description='Sincronización privada y opcional de Excel OneDrive.')
    p.add_argument('--sync', action='store_true', help='Subir cambios con credenciales autorizadas')
    args = p.parse_args()
    if args.sync and os.environ.get('MCA_ONEDRIVE_AUTHORIZED') != 'true':
        raise RuntimeError('El envío requiere autorización explícita MCA_ONEDRIVE_AUTHORIZED=true.')
    sync(dry_run=not args.sync)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('No se completó: ' + str(exc).split('\n')[0][:180], file=sys.stderr)
        sys.exit(1)
