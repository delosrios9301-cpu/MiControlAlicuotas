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
# Textos coherentes con OneDrive en nube, sin depender de una PC encendida.
for before, after in [
    ("Los cambios aparecen cuando se conecta la PC, se sincroniza Firebase y la aplicación del teléfono está abierta. No son alícuotas congeladas confirmadas.", "Las modificaciones guardadas en OneDrive podrán verse desde Android después de sincronizarse en Firebase, sin mantener la PC encendida. También se admiten capturas desde el equipo Windows. Ningún registro confirma por sí solo la congelación."),
    ("No se han sincronizado filas de Excel. Primero inicia sesión en la misma cuenta Firebase en Windows y Android, y autoriza el envío desde la PC.", "Todavía no hay filas sincronizadas. La conexión privada de OneDrive debe estar autorizada y activada; también puedes recibir capturas desde Windows.")
]:
    if source.count(before) != 1:
        raise RuntimeError('No coincide el texto esperado de Sincronización; se detiene publicación.')
    source = source.replace(before, after, 1)
# Una ausencia observada no demuestra que la fila fue borrada del libro.
old_status = 'Fila vaciada en Excel'
if source.count(old_status) != 1:
    raise RuntimeError('No existe el indicador de fila ausente para corregir.')
source = source.replace(old_status, 'Fila no encontrada en la última revisión; datos anteriores conservados', 1)
old_label = "guide:'Guía'})[name]"
if source.count(old_label) != 1:
    raise RuntimeError('No existe el diccionario de campos del historial.')
source = source.replace(old_label, "guide:'Guía',_cleared:'Fila ausente'})[name]", 1)
path.write_text(source,encoding='utf-8')
print('Historial de Excel visible en Sincronización, con detalle plegable por fila.')
