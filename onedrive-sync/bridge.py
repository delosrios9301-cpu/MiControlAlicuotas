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

def row_fingerprints(rows):
    """Huellas sin datos personales para detectar filas reordenadas o insertadas."""
    fields = ('study', 'sampleType', 'subject', 'visit', 'barcode', 'aliquotType', 'pivot')
    index = {}
    for sheet, number, data in rows:
        key = hashlib.sha256(canon([sheet] + [str(data.get(field, '')).strip().upper()
                                            for field in fields]).encode('utf-8')).hexdigest()
        index.setdefault(key, []).append(f'{sheet}:{number}')
    return {key: sorted(locations) for key, locations in sorted(index.items())}

def validate_no_moved_rows(state_doc, current_index):
    raw = (state_doc or {}).get('fields', {}).get('rowFingerprints', {}).get('stringValue')
    if not raw:
        return
    try:
        old_index = json.loads(raw)
    except (TypeError, ValueError):
        raise RuntimeError('Estado anterior de filas inválido; importación detenida.')
    if not isinstance(old_index, dict):
        raise RuntimeError('Estado anterior de filas inválido; importación detenida.')
    for fingerprint, previous_locations in old_index.items():
        now = current_index.get(fingerprint)
        if now is not None and previous_locations != now:
            raise RuntimeError('Excel con filas insertadas o reordenadas. '
                               'Sincronización detenida para evitar duplicados.')

def missing_row_positions(state_doc, rows):
    """Filas anteriormente presentes que ya no aparecen en el XLSX.

    Nunca interpretarlas como borrados definitivos: pueden haberse vaciado,
    ocultado por un fallo de guardado o eliminado. Se conservan en el espejo.
    """
    raw = (state_doc or {}).get('fields', {}).get('rowFingerprints', {}).get('stringValue')
    if not raw:
        return []
    try:
        old_index = json.loads(raw)
        if not isinstance(old_index, dict):
            raise ValueError('Formato incorrecto')
        previous_locations = {
            location
            for locations in old_index.values()
            for location in locations
        }
        if not all(
            isinstance(loc, str) and loc.rpartition(':')[0] in SHEETS
            and loc.rpartition(':')[2].isdigit()
            and int(loc.rpartition(':')[2]) >= 4
            for loc in previous_locations
        ):
            raise ValueError('Identidad de fila inválida')
    except (TypeError, ValueError):
        raise RuntimeError('Historial anterior de ubicaciones inválido; sincronización detenida.')
    current_locations = {f'{sheet}:{number}' for sheet, number, _ in rows}
    # Una hoja totalmente vacía puede ser un fallo de exportación: detener.
    if previous_locations and not current_locations:
        raise RuntimeError('El Excel apareció completamente vacío; no se actualizó ningún registro.')
    # Si falta una pestaña entera, no marcar sus filas: podría ser un error
    # de lectura, un guardado incompleto o un cambio en el esquema del libro.
    previous_sheets = {loc.rpartition(':')[0] for loc in previous_locations}
    current_sheets = {sheet for sheet, _, _ in rows}
    if previous_sheets - current_sheets:
        raise RuntimeError('Una hoja antes utilizada no aparece con filas; '
                           'se detuvo la actualización para proteger los registros.')
    missing = previous_locations - current_locations
    return sorted(
        ((loc.rpartition(':')[0], int(loc.rpartition(':')[2])) for loc in missing),
        key=lambda x: (x[0], x[1]),
    )

def mirror_missing_payload(rid, source_name, sheet, number, previous):
    """No borrar datos anteriores. Señalar explícitamente una fila ausente."""
    if not previous or not isinstance(previous.get('data'), dict):
        raise RuntimeError('No existe una copia previa verificable de la fila ausente.')
    data = dict(previous['data'])
    data['_cleared'] = True
    entry = mirror_payload(rid, source_name, sheet, number, data, previous)
    entry['reviewNote'] = ('La fila no aparece en la última revisión del Excel. '
                           'Comprueba si se vació o movió; los datos previos se conservaron.')
    return entry

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
    """Registrar qué campos cambiaron en cada lectura del Excel.

    Este historial conserva únicamente el nombre de los campos modificados,
    no copias de los valores clínicos anteriores. Un cambio no guardado o
    sobrescrito entre dos revisiones de OneDrive no puede recuperarse.
    """
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    previous = (prior or {}).get('data') or {}
    changed_fields = sorted(
        key for key in data
        if key != 'sheetKind' and (
            prior is None and str(data.get(key, '')).strip()
            or prior is not None and data.get(key) != previous.get(key)
        )
    )
    history = (prior or {}).get('changeHistory')
    if not isinstance(history, list):
        history = []
    # Limitar tamaño y normalizar datos antiguos; no incluir valores de pacientes.
    history = [
        {'at': item['at'], 'fields': item['fields'], 'kind': item['kind']}
        for item in history[-49:]
        if isinstance(item, dict)
        and isinstance(item.get('at'), str)
        and isinstance(item.get('fields'), list)
        and item.get('kind') in ('registro_inicial', 'actualizacion')
    ]
    history.append({
        'at': now,
        'kind': 'actualizacion' if prior else 'registro_inicial',
        'fields': changed_fields,
    })
    return {
        'id': rid, 'sourceBook': source_name, 'sourceSheet': sheet,
        'sourceRow': number, 'sourceEventId': 0, 'timestamp': now,
        'data': data, 'importedAt': (prior or {}).get('importedAt'),
        'importedRecordId': (prior or {}).get('importedRecordId'),
        'dismissedAt': None,
        'reviewNote': 'El Excel cambió después de revisión.' if prior and prior.get('reviewedAt') else None,
        'reviewedAt': None, 'sourceOrigin': 'onedrive',
        'sourceLocalId': f'{sheet}|{number}',
        'changedFields': changed_fields,
        'changeHistory': history,
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

def write_state(url, etag, index):
    fingerprints = canon(index)
    if len(fingerprints.encode('utf-8')) > 700000:
        raise RuntimeError('Demasiadas filas para guardar la huella segura del Excel.')
    firestore('PATCH', url, {'fields': {
        'etag': {'stringValue': etag},
        'rowFingerprints': {'stringValue': fingerprints},
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
    index = row_fingerprints(rows)
    validate_no_moved_rows(old, index)
    missing = missing_row_positions(old, rows)
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
    for sheet, number in missing:
        rid = source_id(drive_id, item_id, sheet, number)
        before = firestore('GET', doc_url(base, rid), missing_ok=True)
        previous, timestamp = previous_data(before)
        if previous and isinstance(previous.get('data'), dict) and previous['data'].get('_cleared'):
            continue
        entry = mirror_missing_payload(rid, info['name'], sheet, number, previous)
        if len(canon(entry).encode()) > 890000:
            raise ValueError('Registro demasiado grande; el historial no fue actualizado.')
        put_mirror(base, rid, entry, timestamp)
        changed += 1
    write_state(state, etag, index)
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
