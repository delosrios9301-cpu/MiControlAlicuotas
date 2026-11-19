import io
import unittest
from unittest import mock
from types import SimpleNamespace
from openpyxl import Workbook
from bridge import extract_rows, source_id, row_data, mirror_payload, validated_rclone_path, rclone_file, source_reference

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

    def test_first_column_blank_does_not_fail(self):
        # Las primeras celdas de una fila pueden estar vacías sin invalidar los demás campos.
        wb=Workbook()
        sh=wb.active
        sh.title='ALMACENAMIENTO DE ALICUOTAS'
        sh['D4']='FICTICIO-SIN-COLUMNA-B'
        data=io.BytesIO()
        wb.save(data)
        rows=extract_rows(data.getvalue())
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][1],4)
        self.assertEqual(rows[0][2]['subject'],'FICTICIO-SIN-COLUMNA-B')

    def test_rclone_rejects_unsafe_paths(self):
        for path in ('../pacientes.xlsx', '/privado.xlsx', 'libro.xlsm', 'C:/datos.xlsx', 'carpeta\\\\datos.xlsx', ''):
            with self.subTest(path=path), mock.patch.dict('os.environ', {'ONEDRIVE_RELATIVE_PATH':path}):
                with self.assertRaises(ValueError):
                    validated_rclone_path()

    def test_rclone_fetch_uses_selected_excel_only(self):
        with mock.patch.dict('os.environ',{
            'ONEDRIVE_RELATIVE_PATH':'Trabajo/Copia.xlsx',
            'RCLONE_CONFIG_ONEDRIVE_TOKEN':'{"refresh_token":"test-ficticio"}',
            'ONEDRIVE_DRIVE_ID':'drive-prueba',
            'ONEDRIVE_ACCESS_METHOD':'rclone'}), mock.patch(
                'bridge.subprocess.run',
                return_value=SimpleNamespace(returncode=0,stdout=self.workbook(),stderr=b'')) as subprocess_mock:
            info,content=rclone_file()
            self.assertEqual(info['name'],'Copia.xlsx')
            self.assertEqual(len(extract_rows(content)),1)
            args=subprocess_mock.call_args.args[0]
            self.assertEqual(args[-1], 'onedrive:Trabajo/Copia.xlsx')
            self.assertEqual(source_reference(),('drive-prueba','path:Trabajo/Copia.xlsx'))

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
