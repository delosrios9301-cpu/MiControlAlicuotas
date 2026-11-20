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
  'no contar vínculo pendiente como alícuota pendiente': "S.cloudPending=rows[6].filter(job=>job.table!=='workbooks'||window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled).length;" in app,
  'preservar cola original para sincronizar después': "new Set(['records','shifts','freezers','audit','mirrors','workbooks'])" in db,
  'migración no destructiva': 'DB_VERSION=4' in db and "db.createObjectStore(name,{keyPath})" in db,
  'backup de vínculo': "workbooks:await all('workbooks')" in db,
  'restaurar backup antiguo': "Array.isArray(json.workbooks)?json.workbooks:[]" in db,
  'versión pwa': "mis-alicuotas-shell-github-20261120-excel-central" in sw,
}
for name,ok in checks.items():
    if not ok:
        raise SystemExit('FALLÓ: '+name)
    print('CORRECTO:',name)
assert len(app)<150000 and len(db)<40000
assert '.xlsx' not in [p.suffix.lower() for p in Path('site').rglob('*') if p.is_file()]
print('Mi Excel: pruebas estáticas aprobadas; pendiente prueba real de acceso Microsoft/Firebase.')
