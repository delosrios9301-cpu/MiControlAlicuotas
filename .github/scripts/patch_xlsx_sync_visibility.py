#!/usr/bin/env python3
"""Aclara los contadores y vías de importación: local XLSX vs Firebase remoto."""
from pathlib import Path
p=Path('site/app.js')
s=p.read_text(encoding='utf8')
def patch(old,new,label):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(f'{label}: esperada 1 coincidencia, se hallaron {n}')
 s=s.replace(old,new,1)
patch("Cambios de Excel detectados en Windows y visualizados en otros dispositivos",
 "Capturas Excel locales y sincronización entre dispositivos",'encabezado')
patch("La PC envía cambios autorizados mediante Firebase; el teléfono no lee Excel directamente.",
 "Para leer tu Excel en el teléfono, entra en Mi Excel y selecciona el archivo XLSX. Las filas compartidas por Firebase se contabilizan aparte.",'instrucción Android')
patch(" const enabled=Boolean(S.settings.excelMirrorEnabled);",
 " const enabled=Boolean(S.settings.excelMirrorEnabled);\n const localExcelCount=S.captures.filter(c=>c.sourceOrigin==='manual-xlsx').length;",'recuento local')
patch(" consentUI+\n `${renderCloudPanel()}<section",
 """ consentUI+
 `<p class="small muted">Capturas XLSX guardadas en este dispositivo: <strong>${number(localExcelCount)}</strong>. Este contador es distinto de «filas compartidas» desde Firebase. Puedes revisarlas más abajo en «Capturas Excel para revisar». ${button('nav-excel','Ver mi Excel','btn small')}</p>`+
 `${renderCloudPanel()}<section""",'recuento separado')
sw=Path('site/sw.js')
cache=sw.read_text(encoding='utf8')
old='mis-alicuotas-shell-github-20261120-xlsx-result'
if cache.count(old)!=1:raise RuntimeError('No se encontró versión PWA esperada para actualizar.')
sw.write_text(cache.replace(old,'mis-alicuotas-shell-github-20261120-capturas-locales-visibles'),encoding='utf8')
p.write_text(s,encoding='utf8')
print('Contadores XLSX y Firebase diferenciados; instrucciones Android corregidas.')
