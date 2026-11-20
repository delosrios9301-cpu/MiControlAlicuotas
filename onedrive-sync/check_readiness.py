#!/usr/bin/env python3
"""Comprueba solo presencia de prerequisitos. No abre OneDrive ni Firestore.
No imprime secretos, IDs de cuenta, rutas ni datos clínicos.
"""
import os
from pathlib import Path

def is_true(name):
    return os.getenv(name, '').strip().lower() == 'true'
def present(name):
    return bool(os.getenv(name, '').strip())

mode=os.getenv('ACCESS_METHOD','graph').strip().lower() or 'graph'
checks=[
  ('Autorización expresa para sincronizar datos', is_true('USER_AUTHORIZED')),
  ('Integración automática activada deliberadamente', is_true('SYNC_ENABLED')),
  ('Cuenta de Firebase para recibir capturas', present('OWNER_UID')),
  ('Identidad federada de Google Cloud', present('WIF_PROVIDER') and present('SYNC_SERVICE_ACCOUNT')),
  ('Identificador de OneDrive', present('DRIVE_ID')),
]
if mode=='rclone':
  checks += [
    ('Ruta de libro Excel privado',present('RELATIVE_PATH')),
    ('Autorización Microsoft de solo lectura',is_true('HAS_RCLONE_TOKEN')),
  ]
elif mode=='graph':
  checks += [
    ('Identificador privado del Excel',present('ITEM_ID')),
    ('Configuración de aplicación Microsoft',present('CLIENT_ID')),
    ('Autorización Microsoft de solo lectura',is_true('HAS_REFRESH_TOKEN')),
  ]
else:
  checks += [('Método autorizado (graph o rclone)',False)]

ready=all(ok for _,ok in checks)
print('Diagnóstico de requisitos OneDrive → Firebase (sin acceso a registros):')
for name,ok in checks:
    print(('OK: ' if ok else 'PENDIENTE: ')+name)
print('RESULTADO: '+('REQUISITOS PRESENTES; FALTA PRUEBA PRIVADA AUTORIZADA' if ready else 'NO ACTIVAR SIN COMPLETAR AUTORIZACIONES'))
summary=os.getenv('GITHUB_STEP_SUMMARY')
if summary:
  with Path(summary).open('a',encoding='utf8') as out:
    out.write('## Requisitos de conexión automática OneDrive → Firebase\n\n')
    for name,ok in checks:
      out.write(f'- {"Configurado" if ok else "Pendiente"}: {name}\n')
    out.write('\n**'+('Requisitos presentes: validar permisos y prueba ficticia antes de activar.' if ready else 'Integración aún no lista para activarse.')+'**\n')
