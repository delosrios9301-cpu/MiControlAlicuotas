#!/usr/bin/env python3
"""Asegura visibilidad persistente del resultado XLSX sin tocar datos clínicos.

Se ejecuta después de patch_xlsx_import.py y falla si cambia la interfaz esperada.
"""
from pathlib import Path

p=Path('site/app.js')
s=p.read_text(encoding='utf-8')
def patch(old,new,label):
 global s
 n=s.count(old)
 if n!=1:
  raise RuntimeError(f'Estado XLSX [{label}]: se esperaba 1 coincidencia, halladas {n}')
 s=s.replace(old,new,1)

patch(
 "const record=S.workbooks.find(w=>w.id==='principal'),url=validOneDriveLink(record?.url),c=cloud.getCloudStatus();",
 """const record=S.workbooks.find(w=>w.id==='principal'),url=validOneDriveLink(record?.url),c=cloud.getCloudStatus();
 const imported=S.captures.filter(x=>x.sourceOrigin==='manual-xlsx');
 const pendingReview=imported.filter(x=>!x.importedAt&&!x.dismissedAt).length;
 const report=S.settings.xlsxImportReport;""",
 "contador del Excel"
)
patch(
 '<section class="card"><h3>Disponibilidad desde otros dispositivos</h3>',
 '''<section class="card" id="excelImportResult"><div class="card-head"><h3>Resultado de la importación</h3><span class="badge ${report?.kind==='error'?'warn':imported.length?'blue':'gray'}">${report?.kind==='error'?'Revisar error':imported.length?'Capturas guardadas':'Sin capturas'}</span></div>
 <p class="small">${report?e(report.message):'Todavía no se ha confirmado ninguna lectura del archivo XLSX en este dispositivo.'}</p>
 <div class="cloud-grid"><div class="cloud-metric"><strong>${number(imported.length)}</strong><small>Filas de Excel guardadas localmente</small></div><div class="cloud-metric"><strong>${number(pendingReview)}</strong><small>Por revisar</small></div></div>
 <p class="small muted">Las capturas no aparecen todavía en el inventario: primero debes revisarlas. La importación local tampoco significa que el Excel esté sincronizado automáticamente con OneDrive o Firebase.</p>
 ${imported.length?button('nav-sync','Ver capturas Excel para revisar','btn primary'):''}</section>
 <section class="card"><h3>Disponibilidad desde otros dispositivos</h3>''',
 "tarjeta de estado permanente"
)
patch(
 """if(!pending.length&&blocked===0){
  toast('No hay filas nuevas: '+unchanged+' ya habían sido leídas.');
  return;
 }""",
 """if(!pending.length&&blocked===0){
  await put('settings',{key:'xlsxImportReport',value:{
   kind:'unchanged',at:now(),created:0,updated:0,unchanged,blocked:0,
   message:'Excel leído correctamente. No había filas nuevas; '+unchanged+' filas ya estaban guardadas en Capturas Excel.'
  }});
  await refresh();navigate('mi-excel');
  toast('Excel leído: sin filas nuevas, '+unchanged+' ya guardadas.');
  return;
 }""",
 "resultado sin filas nuevas"
)
patch(
 """if(pending.length)await batch('captures',pending);
 await refresh();
 navigate('sincronizacion');""",
 """if(pending.length)await batch('captures',pending);
 await put('settings',{key:'xlsxImportReport',value:{
  kind:blocked?'warning':'success',at:now(),created,updated,unchanged,blocked,
  message:'Excel leído: '+created+' filas nuevas, '+updated+' actualizadas, '+unchanged+' sin cambios'+(blocked?', '+blocked+' bloqueadas para evitar duplicados':'')+'.'
 }});
 await refresh();
 navigate('mi-excel');""",
 "guardar resultado después de lectura"
)
patch(
 """try{await importXlsxOnDevice(file);}catch(err){toast('No se pudo leer el Excel: '+(err?.message||'archivo incompatible'),true);}""",
 """try{await importXlsxOnDevice(file);}catch(err){
  const reason=String(err?.message||'archivo incompatible').slice(0,300);
  try{
   await put('settings',{key:'xlsxImportReport',value:{
    kind:'error',at:now(),created:0,updated:0,unchanged:0,blocked:0,
    message:'No se importaron filas. '+reason
   }});
   await refresh();navigate('mi-excel');
  }catch(_){}
  toast('No se pudo leer el Excel: '+reason,true);
 }""",
 "mostrar error persistente"
)
patch(
 "case'nav-sync':navigate('sincronizacion');return;",
 "case'nav-sync':closeModal();navigate('sincronizacion');return;",
 "abrir revisión desde resumen y cerrar cuadro"
)
patch(
 "${button('close-modal','Revisar capturas','btn primary')}",
 "${button('nav-sync','Revisar capturas','btn primary')}",
 "el cuadro lleva a capturas"
)
sw=Path('site/sw.js')
cache=sw.read_text(encoding='utf-8')
old='mis-alicuotas-shell-github-20261120-selector-excel-visible'
if cache.count(old)!=1:raise RuntimeError('Caché Android no coincide con versión esperada.')
cache=cache.replace(old,'mis-alicuotas-shell-github-20261120-xlsx-result')
sw.write_text(cache,encoding='utf-8')
p.write_text(s,encoding='utf-8')
print('Resultado XLSX visible y persistente; capturas y datos existentes conservados.')
