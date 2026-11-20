#!/usr/bin/env python3
"""Habilita importación XLSX local en Android desde el menú Mi Excel.
No borra, sobrescribe ni transmite datos clínicos. Fallar ante paquete inesperado.
"""
from pathlib import Path
file=Path('site/app.js')
s=file.read_text(encoding='utf8')
def replace(old,new,tag):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(f'{tag}: esperaba 1 coincidencia, había {n}')
 s=s.replace(old,new,1)
input_html='''<section class="card"><div class="card-head"><h3>Leer registros del Excel</h3><span class="badge blue">En este dispositivo</span></div><p class="small muted">Selecciona tu XLSX desde OneDrive o Descargas. La app leerá las hojas de alícuotas y salidas sin cambiar el archivo. Las filas se mostrarán para revisión; no se confirma ninguna congelación automáticamente.</p><label for="manualExcelInput" class="btn primary">Seleccionar Excel para importar</label><input id="manualExcelInput" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" hidden><p class="small muted mt">Puedes volver a seleccionar el mismo archivo después de guardar cambios; se revisan las filas nuevas o modificadas sin crear duplicados. Por ahora esta lectura es manual, no sincronización automática de OneDrive.</p></section>'''
replace('''<section class="card"><h3>Disponibilidad desde otros dispositivos</h3>''',input_html+'''<section class="card"><h3>Disponibilidad desde otros dispositivos</h3>''','sección Mi Excel')
# Leer archivo y almacenar capturas solo locales, evitando identidades reemplazadas o filas movidas.
s+='''

// Importación de XLSX: lectura local de los bytes, sin POST ni subida de archivo.
const captureIdentity=a=>['study','sampleType','subject','visit','barcode','aliquotType','pivot'].map(k=>String(a?.[k]??'').trim().toUpperCase()).join('|');
async function importXlsxOnDevice(file){
 if(!file||file.size>15000000)throw Error('El Excel debe pesar como máximo 15 MB.');
 const {readAliquotXlsx}=await import('./xlsx-reader.js');
 const parsed=await readAliquotXlsx(file);
 if(parsed.rows.length===0)throw Error('No se encontraron filas de alícuotas en las hojas reconocidas.');
 // Antes de guardar, detectar movimiento de filas o sustitución accidental.
 const byId=new Map(S.captures.map(c=>[c.id,c]));
 const byIdentity=new Map();
 for(const c of S.captures){
  if(c.sourceOrigin!=='manual-xlsx'||c.sourceBook!==file.name)continue;
  const fp=captureIdentity(c.data);
  if(fp.replaceAll('|',''))byIdentity.set(c.sourceSheet+'|'+fp,c.id);
 }
 const pending=[];let unchanged=0,blocked=0,updated=0,created=0;
 const inFile=new Map();
 for(const r of parsed.rows){
  const key='local-xlsx:'+file.name+'|'+r.sheet+'|'+r.row;
  const fp=captureIdentity(r.data),sameSheet=r.sheet+'|'+fp;
  if(inFile.has(sameSheet)){blocked++;continue;}
  inFile.set(sameSheet,true);
  const prev=byId.get(key);
  if(prev&&captureIdentity(prev.data)!==fp){blocked++;continue;}
  const location=byIdentity.get(sameSheet);
  if(location&&location!==key){blocked++;continue;}
  if(prev&&JSON.stringify(prev.data)===JSON.stringify(r.data)){unchanged++;continue;}
  const changes=!!prev;
  pending.push({
   id:key,sourceBook:file.name,sourceSheet:r.sheet,sourceRow:r.row,
   sourceOrigin:'manual-xlsx',sourceEventId:Date.now(),timestamp:now(),
   data:r.data,importedAt:prev?.importedAt||null,
   importedRecordId:prev?.importedRecordId||null,
   dismissedAt:null,reviewedAt:null,
   reviewNote:changes&&prev?.importedAt
    ?'El Excel cambió después de incorporar la fila. Revisa el registro existente antes de decidir qué corregir.'
    :null
  });
  if(changes)updated++;else created++;
 }
 if(!pending.length&&blocked===0){
  toast('No hay filas nuevas: '+unchanged+' ya habían sido leídas.');
  return;
 }
 if(pending.length)await batch('captures',pending);
 await refresh();
 navigate('sincronizacion');
 modal('Importación de Excel revisable','No se modificó el archivo original ni se confirmaron congelaciones.',`
  <div class="list-cards">
   <div class="list-card"><strong>${created} capturas nuevas</strong></div>
   <div class="list-card"><strong>${updated} filas actualizadas para revisión</strong></div>
   <div class="list-card"><strong>${unchanged} filas sin cambios</strong></div>
   ${blocked?`<div class="notice-warn">${blocked} filas no incorporadas por posible duplicación, reordenamiento o cambio de identidad. Revisa el Excel antes de importarlas.</div>`:''}
  </div>
  <p class="small muted">Ve a «Capturas Excel para revisar». Los registros aceptados se incorporan como pendientes de congelación y podrán sincronizarse por Firebase si tu cuenta y sus reglas lo permiten.</p>
  <div class="form-actions">${button('close-modal','Revisar capturas','btn primary')}</div>`);
}
document.addEventListener('change',async ev=>{
 if(ev.target.id!=='manualExcelInput')return;
 const element=ev.target,file=element.files?.[0];
 element.value='';
 if(!file)return;
 if(!confirm('Se leerán las hojas del Excel en este dispositivo y se conservarán como capturas para revisión. No se publicará el archivo ni se confirmará una congelación. ¿Continuar?'))return;
 try{await importXlsxOnDevice(file);}catch(err){toast('No se pudo leer el Excel: '+(err?.message||'archivo incompatible'),true);}
});
'''
# El lector también estará disponible sin conexión después de una visita online.
sw=Path('site/sw.js')
cache=sw.read_text(encoding='utf8')
tag="mis-alicuotas-shell-github-20261120-firebase-pendientes"
if cache.count(tag)!=1:raise RuntimeError('Versión esperada del caché PWA no coincide.')
cache=cache.replace(tag,'mis-alicuotas-shell-github-20261120-importacion-xlsx')
anchor="'./app.js',"
if cache.count(anchor)!=1:raise RuntimeError('No se halló lista de recursos PWA.')
cache=cache.replace(anchor,anchor+"'./xlsx-reader.js',")
sw.write_text(cache,encoding='utf8')
file.write_text(s,encoding='utf8')
print('Importación XLSX local preparada: revisión explícita, sin duplicar ni confirmar alícuotas.')
