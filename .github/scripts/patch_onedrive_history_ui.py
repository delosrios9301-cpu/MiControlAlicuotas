#!/usr/bin/env python3
"""Añadir historial plegable de los cambios detectados sin exponer valores anteriores."""
from pathlib import Path
import json
change = json.loads("{\"old\":\"</small></div>${button('review-mirror'\",\"new\":\"</small>${Array.isArray(c.changeHistory)&&c.changeHistory.length?'<details class=\\\"mt\\\"><summary>Historial detectado ('+c.changeHistory.length+')</summary>'+c.changeHistory.slice(-8).reverse().map(h=>'<p class=\\\"small\\\">'+e(t(h.at))+' · '+e(h.kind==='registro_inicial'?'Registro inicial':'Actualización')+' · '+e((Array.isArray(h.fields)?h.fields:[]).map(excelFieldLabel).join(', ')||'Sin campos')+'</p>').join('')+'</details>':''}</div>${button('review-mirror'\",\"helper\":\"function excelFieldLabel(name){return ({study:'Estudio',sampleType:'Tipo de muestra',subject:'Sujeto',visit:'Visita',barcode:'Código',aliquotType:'Tipo de alícuota',pivot:'Pivote',qty:'Cantidad',freezer:'Congelador',drawer:'Gaveta',box:'Caja',position:'Posición',operator:'Responsable',entryDate:'Fecha de ingreso',note:'Observaciones',cyclicCount:'Conteo cíclico',cyclicDate:'Fecha del conteo',cyclicOperator:'Responsable del conteo',cyclicNote:'Observación de conteo',validation:'Validación',validationDate:'Fecha de validación',validationOperator:'Responsable de validación',validationNote:'Observación de validación',trackingCode:'Código de seguimiento',exitDate:'Fecha de salida',guide:'Guía'})[name]||String(name||'—');}\",\"marker\":\"function renderSync(){\"}")
path = Path('site/app.js')
source = path.read_text(encoding='utf-8')
if source.count(change['old']) != 1 or source.count(change['marker']) != 1:
    raise RuntimeError('No coincide la plantilla de espejos; se detiene publicación sin modificarla.')
source = source.replace(change['old'],change['new'],1)
source = source.replace(change['marker'],change['helper']+'\n'+change['marker'],1)
path.write_text(source,encoding='utf-8')
print('Historial de Excel visible en Sincronización, con detalle plegable por fila.')
