#!/usr/bin/env python3
"""Pruebas de regresión de la pantalla Mi Excel. No utiliza datos clínicos."""
from pathlib import Path
app=Path('site/app.js').read_text(encoding='utf-8')
db=Path('site/db.js').read_text(encoding='utf-8')
cloud=Path('site/cloud.js').read_text(encoding='utf-8')
html=Path('site/index.html').read_text(encoding='utf-8')
sw=Path('site/sw.js').read_text(encoding='utf-8')
checks={
  'navegación': 'data-page="mi-excel"' in html,
  'pantalla central': "function renderExcelHub()" in app and "id=\"excelHubForm\"" in app,
  'botón de acceso': 'Abrir y editar Excel' in app and 'Abrir para descargar' in app,
  'dominios restringidos': "const hosts=new Set(['onedrive.live.com','1drv.ms'" in app,
  'no copia de xlsx': 'La app guardará la referencia' in app and 'no una copia del Excel' in app,
  'sync de vínculo': "'workbooks'" in cloud and "'workbooks'" in db,
  'protección sin reglas': "job.table==='workbooks'&&!config.workbookSyncEnabled" in cloud,
  'aviso de vínculo Excel separado': 'Vínculo de Mi Excel guardado solo en este dispositivo' in app,
  'no contar vínculo pendiente como alícuota pendiente': "S.cloudPending=rows[6].filter(job=>job.table!=='workbooks'||window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled).length;" in app,
  'preservar cola original para sincronizar después': "new Set(['records','shifts','freezers','audit','mirrors','workbooks'])" in db,
  'migración no destructiva': 'DB_VERSION=4' in db and "db.createObjectStore(name,{keyPath})" in db,
  'backup de vínculo': "workbooks:await all('workbooks')" in db,
  'restaurar backup antiguo': "Array.isArray(json.workbooks)?json.workbooks:[]" in db,
  'selector Android visible': 'id="manualExcelInput"' in app and 'aria-label="Elegir archivo XLSX desde el teléfono"' in app and 'type="file"' in app and 'hidden><p class="small muted mt">Puedes volver' not in app,
  'Firebase indica autenticación verdadera': 'Cuenta Firebase sin sesión' in app and 'Cuenta Firebase autenticada' in app,
  'recuento local Excel visible': 'Capturas XLSX guardadas en este dispositivo' in app,
  'resultado Excel persistente': 'excelImportResult' in app and "key:'xlsxImportReport'" in app,
  'errores de Excel persistentes': "kind:'error'" in app and "No se importaron filas." in app,
  'enlace a revisión funcional': "button('nav-sync','Revisar capturas','btn primary')" in app,
  'importación local XLSX': 'readAliquotXlsx' in app and Path('site/xlsx-reader.js').is_file(),
  'no congela Excel': "Las filas se mostrarán para revisión" in app,
  'capturas locales': "await batch('captures',pending)" in app,
  'contra filas duplicadas': "captureIdentity(prev.data)!==fp" in app,
  'versión pwa': "mis-alicuotas-shell-github-20261120-capturas-locales-visibles" in sw,
}
for name,ok in checks.items():
    if not ok:
        raise SystemExit('FALLÓ: '+name)
    print('CORRECTO:',name)
assert len(app)<150000 and len(db)<40000
assert '.xlsx' not in [p.suffix.lower() for p in Path('site').rglob('*') if p.is_file()]
print('Mi Excel: pruebas estáticas aprobadas; pendiente prueba real de acceso Microsoft/Firebase.')
