# Vincular una vez OneDrive personal de Outlook

Esta utilidad **no ejecuta el capturador Excel en Windows**, no sincroniza datos clínicos y no necesita Azure/Cevaxin. Sirve para obtener la autorización inicial que exige Microsoft.

## Cómo usarlo (Windows, solo la primera vez)

1. En GitHub abre el repositorio **MiControlAlicuotas** y selecciona **Code → Download ZIP**. Extrae el ZIP en tu computadora Windows.
2. En la carpeta extraída abre `onedrive-sync` y haz doble clic en `CONECTAR-ONEDRIVE-WINDOWS.cmd`. Si Windows muestra una advertencia de seguridad, **no la ignores**: comprueba que el script procede del repositorio del proyecto y revisa su contenido.
3. El asistente intentará instalar **rclone** mediante `winget` si no existe. Cuando se abra Microsoft, inicia sesión **solo con tu Outlook personal** y autoriza la lectura. Si aparece Cevaxin o una suscripción de pago, cancela.
4. El asistente comprobará que se haya conectado un OneDrive **personal** con permisos de lectura. No mostrará claves ni tokens en pantalla.

**Resultado esperado:** `ONEDRIVE PERSONAL AUTORIZADO LOCALMENTE`.

## Qué pasa después

- La autorización queda **únicamente en tu PC Windows** hasta que se transfiera de manera segura a los secretos de GitHub; esto **no activa todavía** ninguna transferencia del Excel a Firebase.
- Para la sincronización en la nube sigue faltando guardar de forma privada `ONEDRIVE_RCLONE_TOKEN` y la identificación de la unidad, obtener la ruta exacta del XLSX y configurar la autenticación WIF de Firebase.
- No publiques, pegues en mensajes ni compartas el archivo local `%LOCALAPPDATA%\MiControlAlicuotas\onedrive-personal-rclone.conf`: contiene la credencial de acceso a OneDrive.
- La app web de GitHub Pages seguirá mostrando **OneDrive pendiente de autorización**, hasta que el flujo de nube se active y se valide con un Excel ficticio. No se añaden ni borran registros automáticamente.

## Privacidad y límites

La sesión de rclone puede acceder a varios archivos de tu OneDrive; **no se restringe por Microsoft a un solo XLSX**. El lector del proyecto está programado para descargar únicamente la ruta autorizada, con una cuenta personal separada de Cevaxin. El archivo local de credenciales se debe conservar privado y se puede revocar el permiso desde el panel de permisos de la cuenta Microsoft.

La sincronización programada comprueba cambios en intervalos de unos quince minutos, con retrasos posibles de GitHub Actions. No detecta cada tecla ni cada paso intermedio no guardado.
