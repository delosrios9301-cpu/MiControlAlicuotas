#!/usr/bin/env python3
"""Instala acceso al Excel maestro por OneDrive sin almacenar el XLSX en Pages."""
from pathlib import Path
root=Path('site')

def patch(path, old, new):
    p=root/path
    text=p.read_text(encoding='utf8')
    n=text.count(old)
    if n != 1:
        raise RuntimeError(f'{path}: esperaba 1 coincidencia y encontró {n} de {old[:60]!r}')
    p.write_text(text.replace(old,new,1),encoding='utf8')

patch('db.js', "DB_VERSION=3", "DB_VERSION=4")
patch('db.js', "freezers:'id',captures:'id'", "freezers:'id',workbooks:'id',captures:'id'")
patch('db.js', "new Set(['records','shifts','freezers','audit','mirrors'])", "new Set(['records','shifts','freezers','audit','mirrors','workbooks'])")
patch('db.js', "['settings','records','shifts','freezers','audit','mirrors','outbox']", "['settings','records','shifts','freezers','audit','mirrors','workbooks','outbox']")
# Libros enlazados en copia de seguridad opcional; respaldo viejo compatible.
patch('db.js', "freezers:await all('freezers'),captures:", "freezers:await all('freezers'),workbooks:await all('workbooks'),captures:")
patch('db.js', "['records','shifts','freezers','captures','mirrors','audit','settings','outbox','cloudVersions','conflicts']", "['records','shifts','freezers','workbooks','captures','mirrors','audit','settings','outbox','cloudVersions','conflicts']")
patch('db.js', "const tx=db.transaction(['records','shifts','freezers','workbooks','captures','mirrors','audit','settings','outbox','cloudVersions','conflicts'],'readwrite');", "const tx=db.transaction(['records','shifts','freezers','workbooks','captures','mirrors','audit','settings','outbox','cloudVersions','conflicts'],'readwrite');const books=tx.objectStore('workbooks');books.clear();for(const row of (Array.isArray(json.workbooks)?json.workbooks:[]))books.put(row);")
patch('cloud.js', "new Set(['records','shifts','freezers','audit','mirrors'])", "new Set(['records','shifts','freezers','audit','mirrors','workbooks'])")
# Mientras la regla de Firestore no esté desplegada, el vínculo es local y no bloquea otros registros.
patch('cloud.js', "if(!tables.has(job.table))continue;", "if(!tables.has(job.table)||(job.table==='workbooks'&&!config.workbookSyncEnabled))continue;")
patch('app.js', "'reportes','sincronizacion','configuracion'", "'reportes','mi-excel','sincronizacion','configuracion'")
patch('app.js', "freezers:[],captures:[]", "freezers:[],workbooks:[],captures:[]")
patch('app.js', "function renderSettings(){", '''function validOneDriveLink(raw){
 try{
  const u=new URL(String(raw||'').trim());
  const hosts=new Set(['onedrive.live.com','1drv.ms','onedrive.com','www.onedrive.com','office.com','www.office.com','excel.office.com','microsoft365.com','www.microsoft365.com']);
  return u.protocol==='https:'&&!u.username&&!u.password&&hosts.has(u.hostname.toLowerCase())&&u.href.length<=2048?u.href:null;
 }catch(_){return null;}
}
function renderExcelHub(){
 const record=S.workbooks.find(w=>w.id==='principal'),url=validOneDriveLink(record?.url),c=cloud.getCloudStatus();
 return heading('Mi Excel','Un único archivo maestro guardado en tu OneDrive personal')+
 `<section class="card"><div class="card-head"><h3>Excel principal</h3><span class="badge ${url?'blue':'warn'}">${url?'Acceso guardado':'Sin configurar'}</span></div>`+
 (url?`<p><strong>${e(record.name||'Mi libro de alícuotas')}</strong></p><p class="small muted">El archivo original permanece en OneDrive. Al abrirlo iniciarás sesión en Microsoft si hace falta.</p><div class="actions"><a class="btn primary" href="${e(url)}" target="_blank" rel="noopener noreferrer">Abrir y editar Excel</a><a class="btn" href="${e(url)}" target="_blank" rel="noopener noreferrer">Abrir para descargar</a></div>`:
 `<p class="small muted">Abre OneDrive, localiza el Excel que ya utilizas y copia su vínculo privado para guardarlo aquí. No subas el archivo clínico a GitHub.</p><a class="btn primary" href="https://onedrive.live.com/" target="_blank" rel="noopener noreferrer">Abrir mi OneDrive personal</a>`)+
 `<p class="small muted mt">Para descargar el archivo, usa la opción <strong>Descargar</strong> dentro de OneDrive. Descargar una copia no modifica ni reemplaza el Excel maestro.</p></section>`+
 `<section class="card"><h3>${url?'Cambiar vínculo del Excel':'Vincular el Excel que ya tienes'}</h3><form id="excelHubForm" class="stack"><div class="field"><label for="excelBookName">Nombre para identificar el libro</label><input id="excelBookName" name="name" required maxlength="120" value="${e(record?.name||'Control de alícuotas.xlsx')}" placeholder="Control de alícuotas.xlsx"></div><div class="field"><label for="excelBookLink">Vínculo privado de OneDrive</label><input id="excelBookLink" name="url" type="url" required maxlength="2048" inputmode="url" placeholder="https://onedrive.live.com/..." value="${e(record?.url||'')}"></div><div class="notice-warn">Usa un vínculo que requiera tu cuenta Microsoft, no «Cualquier persona con el vínculo». La app guardará la referencia, <strong>no una copia del Excel</strong>.</div><button class="btn primary" type="submit">Guardar acceso a mi Excel</button></form></section>`+
 `<section class="card"><h3>Disponibilidad desde otros dispositivos</h3><p class="small muted">${c.configured&&c.loggedIn&&window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled?'Si las reglas privadas de Firebase están configuradas y la sincronización termina correctamente, el vínculo estará disponible al iniciar sesión con la misma cuenta en otra PC.':'El acceso se guarda en este dispositivo. Para llevar automáticamente el vínculo a otros equipos debes iniciar sesión en Sincronización con tu cuenta Firebase privada y verificar sus permisos; mientras tanto puedes abrir OneDrive directamente desde cualquier computadora.'}</p><div class="actions"><a class="btn" href="https://onedrive.live.com/" target="_blank" rel="noopener noreferrer">Entrar a OneDrive</a>${button('nav-sync','Ver sincronización','btn')}</div><p class="small muted">Esta sección no importa por sí sola las filas del Excel a la app: esa lectura automática requiere autorizar la conexión privada con Microsoft.</p></section>`;
}
function renderSettings(){''')
patch('app.js', "reportes:renderReports,sincronizacion:renderSync", "reportes:renderReports,'mi-excel':renderExcelHub,sincronizacion:renderSync")
patch('app.js', "case'nav-sync':navigate('sincronizacion');return;", "case'nav-sync':navigate('sincronizacion');return;case'nav-excel':navigate('mi-excel');return;")
patch('app.js', "async function onForm(form){const formId=form.getAttribute('id');", '''async function onForm(form){const formId=form.getAttribute('id');
 if(formId==='excelHubForm'){
  const values=new FormData(form),name=String(values.get('name')||'').trim(),url=validOneDriveLink(values.get('url'));
  if(!name||name.length>120)throw Error('Indica el nombre del Excel.');
  if(!url)throw Error('Introduce el vínculo privado de OneDrive personal. No se admiten enlaces externos.');
  const previous=S.workbooks.find(w=>w.id==='principal');
  if(previous?.url&&previous.url!==url&&!confirm('Cambiar el vínculo no modifica el Excel anterior, pero podría apuntar a otro libro. ¿Confirmar cambio?'))return;
  await put('workbooks',{id:'principal',name,url,updatedAt:now()});
  toast('Acceso guardado. Comprueba la sincronización de nube para usarlo en otras PC.');await refresh();return;
 }
''')
patch('app.js', "#modalRoot form,#profileForm", "#modalRoot form,#profileForm,#excelHubForm")
patch('app.js', "'outbox','conflicts','mirrors'].map(all)", "'outbox','conflicts','mirrors','workbooks'].map(all)")
patch('app.js', "S.mirrors=rows[8];S.captureCursor", "S.mirrors=rows[8];S.workbooks=rows[9];S.captureCursor")
# El vínculo privado de Excel permanece local hasta verificar reglas Firestore.
# No contarlo como operación clínica pendiente, sin borrar su trabajo en cola.
patch('app.js', "S.cloudPending=rows[6].length;", "S.cloudPending=rows[6].filter(job=>job.table!=='workbooks'||window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled).length;")
patch('app.js', "${button('nav-sync','⟳ Revisar capturas Excel','btn')}", "${button('nav-sync','⟳ Revisar capturas Excel','btn')}${button('nav-excel','▤ Abrir mi Excel','btn')}")
patch('index.html', '<button data-page="sincronizacion">', '<button data-page="mi-excel"><span class="ico">▤</span>Mi Excel</button><button data-page="sincronizacion">')
# Mostrar el vínculo local por separado: nunca confundirlo con datos clínicos pendientes.
patch('app.js', "cloudPending:0,cloudConflicts:[]", "cloudPending:0,workbookPending:0,cloudConflicts:[]")
patch('app.js', "S.cloudPending=rows[6].filter(job=>job.table!=='workbooks'||window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled).length;", "S.cloudPending=rows[6].filter(job=>job.table!=='workbooks'||window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled).length;S.workbookPending=rows[6].filter(job=>job.table==='workbooks'&&!window.MCA_FIREBASE_CONFIG?.workbookSyncEnabled).length;")
patch('app.js', "const c=cloud.getCloudStatus(),p=S.cloudPending,n=S.cloudConflicts.length;", "const c=cloud.getCloudStatus(),p=S.cloudPending,n=S.cloudConflicts.length,b=S.workbookPending;")
patch('app.js', '<div class="cloud-grid">', '''${b?`<p class="small muted">Vínculo de Mi Excel guardado solo en este dispositivo; su envío entre dispositivos aún no está habilitado. No es un registro clínico pendiente.</p>`:''}<div class="cloud-grid">''')
# Cache bust para que el nuevo enlace aparezca en Android y Windows.
p=root/'sw.js';s=p.read_text(encoding='utf8');lines=s.splitlines(keepends=True)
found=[i for i,line in enumerate(lines) if line.strip().startswith('const CACHE=')]
if len(found)!=1:raise RuntimeError('Falta versión de caché')
lines[found[0]]="const CACHE='mis-alicuotas-shell-github-20261120-excel-central';\n"
p.write_text(''.join(lines),encoding='utf8')
print('Mi Excel integrado en app y menú; no se almacenan bytes de XLSX en Pages ni Firestore.')
