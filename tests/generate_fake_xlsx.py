#!/usr/bin/env python3
"""Libro XLSX de prueba 100% ficticio; se crea solo durante CI."""
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path
out=Path('tests/prueba_xlsx_ficticia.xlsx')
out.parent.mkdir(exist_ok=True)
workbook='''<?xml version="1.0" encoding="utf-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="ALMACENAMIENTO DE ALICUOTAS" sheetId="1" r:id="rId1"/><sheet name="SALIDA DE MUESTRA" sheetId="2" r:id="rId2"/></sheets></workbook>'''
rels='''<?xml version="1.0" encoding="utf-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>'''
strings='''<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>ESTUDIO-PRUEBA</t></si><si><t>SUERO</t></si><si><t>FICTICIO-1</t></si><si><t>V1</t></si><si><t>CODIGO-TEST</t></si><si><t>PRINCIPAL</t></si></sst>'''
sheet1='''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="4"><c r="B4" t="s"><v>0</v></c><c r="C4" t="s"><v>1</v></c><c r="D4" t="s"><v>2</v></c><c r="E4" t="s"><v>3</v></c><c r="F4" t="s"><v>4</v></c><c r="G4" t="s"><v>5</v></c><c r="I4"><v>2</v></c></row></sheetData></worksheet>'''
sheet2='''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="4"><c r="A4" t="s"><v>0</v></c><c r="B4" t="s"><v>1</v></c><c r="C4" t="s"><v>2</v></c><c r="D4" t="s"><v>3</v></c><c r="E4" t="s"><v>4</v></c><c r="F4" t="s"><v>5</v></c><c r="H4"><v>1</v></c></row></sheetData></worksheet>'''
with ZipFile(out,'w',ZIP_DEFLATED) as z:
    for name,content in [('xl/workbook.xml',workbook),('xl/_rels/workbook.xml.rels',rels),('xl/sharedStrings.xml',strings),('xl/worksheets/sheet1.xml',sheet1),('xl/worksheets/sheet2.xml',sheet2)]:
        z.writestr(name,content)
print('Prueba ficticia lista; no hay datos de pacientes.')
