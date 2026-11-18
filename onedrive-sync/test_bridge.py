import io
import unittest
from openpyxl import Workbook
from bridge import extract_rows, source_id, row_data, mirror_payload

class TestOneDriveBridge(unittest.TestCase):
    def workbook(self):
        wb=Workbook()
        ws=wb.active
        ws.title='ALMACENAMIENTO DE ALICUOTAS'
        vals=['ESTUDIO', 'SUERO', 'FICTICIO-1', 'V1', 'CODE-1', 'PRINCIPAL', '', 2, 'CONG-1', 'G1', 'C1', 'P1', 'Prueba', '2026-11-18', '']
        for c,v in enumerate(vals,start=2):
            ws.cell(4,c,v)
        data=io.BytesIO()
        wb.save(data)
        return data.getvalue()

    def test_extract(self):
        rows=extract_rows(self.workbook())
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][0],'ALMACENAMIENTO DE ALICUOTAS')
        self.assertEqual(rows[0][1],4)
        self.assertEqual(rows[0][2]['subject'],'FICTICIO-1')

    def test_no_blank(self):
        self.assertIsNone(row_data('SALIDA DE MUESTRA', ['']*13))

    def test_stable_identifiers(self):
        a=source_id('drive','item','SALIDA DE MUESTRA',4)
        self.assertEqual(a,source_id('drive','item','SALIDA DE MUESTRA',4))
        self.assertNotEqual(a,source_id('drive','item','SALIDA DE MUESTRA',5))

    def test_mirror_no_freezing(self):
        v=mirror_payload('id','ficticio.xlsx','SALIDA DE MUESTRA',4,{'study':'X'})
        self.assertEqual(v['sourceOrigin'],'onedrive')
        self.assertNotIn('status',v)
        self.assertIsNone(v['reviewedAt'])

if __name__ == '__main__':
    unittest.main()
