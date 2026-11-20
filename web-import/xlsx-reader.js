// Lector de XLSX local: no envía contenido a servidores ni utiliza bibliotecas externas.
// Soporta hojas Office Open XML estándar (ZIP), cadenas compartidas y celdas numéricas.
// Las filas se ofrecen para revisión; nunca se confirman congelaciones automáticamente.
const SCHEMAS={
 'ALMACENAMIENTO DE ALICUOTAS':{first:2,fields:['study','sampleType','subject','visit','barcode','aliquotType','pivot','qty','freezer','drawer','box','position','operator','entryDate','note','cyclicCount','cyclicDate','cyclicOperator','cyclicNote','validation','validationDate','validationOperator','validationNote'],kind:'aliquot'},
 'SALIDA DE MUESTRA':{first:1,fields:['study','sampleType','subject','visit','barcode','aliquotType','pivot','qty','trackingCode','exitDate','guide','operator','note'],kind:'exit'}
};
const td=new TextDecoder('utf-8');
function read16(v,p){return v.getUint16(p,true)}
function read32(v,p){return v.getUint32(p,true)}
function xml(bytes){
 const value=td.decode(bytes);
 if(/<!DOCTYPE|<!ENTITY/i.test(value))throw Error('El libro contiene declaraciones XML no admitidas.');
 const doc=new DOMParser().parseFromString(value,'application/xml');
 if(doc.getElementsByTagName('parsererror').length)throw Error('XML no válido en el Excel.');
 return doc;
}
function elements(parent,name){return Array.from(parent.getElementsByTagName(name))}
function textAt(parent,tag){return parent.getElementsByTagName(tag)[0]?.textContent??''}
function columnNumber(ref){const match=/^([A-Z]+)\d+$/i.exec(ref);if(!match)return 0;let n=0;for(const c of match[1].toUpperCase())n=n*26+c.charCodeAt(0)-64;return n}
function excelDate(value){
 if(typeof value!=='number'||!Number.isFinite(value)||value<1||value>120000)return value;
 return new Date(Date.UTC(1899,11,30)+Math.floor(value)*86400000).toISOString().slice(0,10);
}
async function unzip(content){
 const bytes=new Uint8Array(content),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 let end=-1;
 for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--){if(read32(view,i)===0x06054b50){end=i;break}}
 if(end<0)throw Error('El archivo no es un XLSX ZIP válido.');
 if(read16(view,end+4)!==0||read16(view,end+6)!==0)throw Error('No se admiten ZIP de varios volúmenes.');
 const count=read16(view,end+10),offset=read32(view,end+16),entries=new Map();
 if(count>2000||offset>bytes.length)throw Error('Excel con demasiados componentes.');
 let at=offset;
 for(let i=0;i<count;i++){
  if(at+46>bytes.length||read32(view,at)!==0x02014b50)throw Error('Índice XLSX inválido.');
  const method=read16(view,at+10),compressed=read32(view,at+20),original=read32(view,at+24),n=read16(view,at+28),extra=read16(view,at+30),comment=read16(view,at+32),local=read32(view,at+42);
  const name=td.decode(bytes.subarray(at+46,at+46+n));
  if(original>25_000_000||compressed>15_000_000)throw Error('Un componente del Excel supera el límite seguro.');
  if(name.startsWith('xl/')&&/\.xml$/.test(name))entries.set(name,{method,compressed,original,local});
  at+=46+n+extra+comment;
 }
 let decoded=0;
 async function read(name,optional=false){
  const item=entries.get(name);
  if(!item){if(optional)return null;throw Error('Falta un componente obligatorio del Excel.')}
  const {method,compressed,original,local}=item;
  if(local+30>bytes.length||read32(view,local)!==0x04034b50)throw Error('Componente XLSX corrupto.');
  const at=local+30+read16(view,local+26)+read16(view,local+28);
  if(at+compressed>bytes.length)throw Error('Componente XLSX incompleto.');
  const raw=bytes.subarray(at,at+compressed);
  let value;
  if(method===0)value=raw;
  else if(method===8){
   if(typeof DecompressionStream==='undefined')throw Error('Este navegador no admite leer XLSX. Abre la app en Chrome actualizado.');
   try{
    const stream=new Blob([raw]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    value=new Uint8Array(await new Response(stream).arrayBuffer());
   }catch(_){throw Error('No se pudo descomprimir el Excel. Descarga una copia XLSX estándar.')}
  }else throw Error('Compresión XLSX no compatible.');
  if(value.length!==original)throw Error('El contenido XLSX está incompleto.');
  decoded+=value.length;if(decoded>60_000_000)throw Error('Excel demasiado grande para importación segura.');
  return value;
 }
 return read;
}
function cellValue(c,strings){
 const type=c.getAttribute('t')||'';
 if(type==='e')return '';
 if(type==='inlineStr')return textAt(c,'is').trim();
 const value=textAt(c,'v');
 if(type==='s')return strings[Number(value)]??'';
 if(type==='b')return value==='1'?'Sí':'No';
 if(!value)return '';
 if(!['str','d','inlineStr'].includes(type)&&Number.isFinite(Number(value)))return Number(value);
 return value.trim();
}
function sheetRows(doc,strings,name,schema){
 const found=[];
 for(const row of elements(doc,'row')){
  const number=Number(row.getAttribute('r'));
  if(!Number.isInteger(number)||number<4)continue;
  const values=Array(schema.fields.length).fill('');
  for(const cell of elements(row,'c')){
   const col=columnNumber(cell.getAttribute('r')||'');
   const i=col-schema.first;
   if(i>=0&&i<values.length)values[i]=cellValue(cell,strings);
  }
  const data={sheetKind:schema.kind};
  for(let i=0;i<schema.fields.length;i++){
   const key=schema.fields[i];
   let value=values[i];
   if(typeof value==='string')value=value.trim();
   if(key==='qty')value=value===''?'':Number(value);
   if(/Date$/.test(key)&&typeof value==='number')value=excelDate(value);
   data[key]=value;
  }
  if(!['study','subject','barcode'].some(k=>String(data[k]??'').trim()))continue;
  found.push({sheet:name,row:number,data});
  if(found.length>20000)throw Error('La hoja contiene más de 20 000 filas. Divide una copia del Excel.');
 }
 return found;
}
export async function readAliquotXlsx(file){
 if(!file||!file.name.toLowerCase().endsWith('.xlsx'))throw Error('Selecciona un archivo Excel .xlsx.');
 if(!file.size||file.size>15_000_000)throw Error('El archivo debe ser XLSX y pesar como máximo 15 MB.');
 const get=await unzip(await file.arrayBuffer());
 const wb=xml(await get('xl/workbook.xml')),rels=xml(await get('xl/_rels/workbook.xml.rels'));
 const relationships=new Map(elements(rels,'Relationship').map(r=>[r.getAttribute('Id'),r.getAttribute('Target')]));
 const stringsFile=await get('xl/sharedStrings.xml',true),strings=[];
 if(stringsFile){const ss=xml(stringsFile);for(const item of elements(ss,'si'))strings.push(elements(item,'t').map(t=>t.textContent).join(''));}
 const result=[],available=[];
 for(const sheet of elements(wb,'sheet')){
  const name=sheet.getAttribute('name'),schema=SCHEMAS[name];
  if(!schema)continue;
  available.push(name);
  const target=relationships.get(sheet.getAttribute('r:id'));
  if(!target)throw Error('Una hoja de Excel no tiene una referencia válida.');
  const path=target.startsWith('/')?target.slice(1):target.startsWith('xl/')?target:'xl/'+target;
  if(!/^xl\/worksheets\/[a-zA-Z0-9._-]+\.xml$/.test(path))throw Error('Ruta de hoja Excel no válida.');
  const rows=sheetRows(xml(await get(path)),strings,name,schema);
  result.push(...rows);
  if(result.length>20000)throw Error('El Excel supera 20 000 filas; utiliza un archivo más pequeño.');
 }
 if(!available.length)throw Error('El libro no contiene las hojas ALMACENAMIENTO DE ALICUOTAS o SALIDA DE MUESTRA.');
 return {rows:result,sheets:available};
}
