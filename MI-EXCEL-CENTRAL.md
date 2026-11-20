# Mi Excel central — acceso desde cualquier dispositivo

**Objetivo:** usar **un solo archivo XLSX maestro** que permanezca en la cuenta personal OneDrive de Outlook. Se podrá abrir y descargar desde Android y desde cualquier PC en la que se inicie sesión con Microsoft, sin instalar rclone o ejecutar programas localmente.

## Desde el teléfono (configuración inicial, sin PC)
1. Abre https://delosrios9301-cpu.github.io/MiControlAlicuotas/ y entra en **Mi Excel**, mediante el menú o desde la acción de Inicio.
2. Pulsa **Abrir mi OneDrive personal** e inicia sesión en tu Outlook personal.
3. Localiza el Excel original que usas durante el turno; en OneDrive copia el vínculo de acceso **privado** que requiera tu cuenta (nunca un enlace «Cualquier persona con el vínculo»). Confirma que puedes abrirlo con esa misma cuenta.
4. Regresa a **Mi Excel** y pega el vínculo. Pulsa **Guardar acceso a mi Excel**. Solo se guarda la referencia; no se modifica ni copia el XLSX.

## Desde cualquier PC al llegar al turno
- Abre Mi Control de Alícuotas y el apartado **Mi Excel**. Si el vínculo está guardado en ese equipo, pulsa **Abrir y editar Excel** para trabajar con el libro único en Excel para la Web.
- También puedes entrar directamente a https://onedrive.live.com/ con la **misma cuenta Outlook personal** y abrir el Excel maestro, aunque el vínculo todavía no esté sincronizado entre dispositivos.
- Para una copia local, usa **Abrir para descargar → Descargar** en OneDrive. Recuerda: si editas esa copia descargada y no guardas los cambios de vuelta al archivo central, **no aparecerán** en el Excel maestro.

## Lo que funciona y lo que aún no

- ✅ Pantalla **Mi Excel**, guardado seguro del vínculo en el dispositivo, apertura y descarga mediante OneDrive; también sigue disponible el registro manual de alícuotas.
- ✅ La copia verdadera queda en OneDrive, no en GitHub Pages ni en Firebase Storage. No se crean archivos clínicos públicos.
- ⚠️ La sincronización del **vínculo** entre teléfonos y PC mediante Firestore solo será posible cuando estén configurados Firebase Authentication y las reglas privadas de `firebase/firestore.rules`. Por seguridad, la subida de `workbooks` permanece **desactivada** mientras no se active `window.MCA_FIREBASE_CONFIG.workbookSyncEnabled` después de desplegar y verificar esas reglas.
- ⛔ La lectura automática de **filas de Excel → registros en Mi Control de Alícuotas** todavía no funciona: necesita autorización de Microsoft y la conexión privada a Firebase. No se debe afirmar lo contrario.
- ⛔ El sistema no registra cada tecla ni cada cambio no guardado. Evita usar una copia descargada como si fuera el libro central.

**Privacidad:** no envíes el archivo de pacientes ni sus enlaces de edición a un chat, repositorio público ni correo no autorizado. Este módulo guarda una referencia; el archivo seguirá protegido por las credenciales de tu OneDrive personal y por los permisos del enlace.

**Costos:** esta ruta no necesita Firebase Storage, que exige Blaze; se mantiene GitHub Pages, OneDrive personal y Firebase Spark. Sus límites de almacenamiento y operación siguen aplicándose.
