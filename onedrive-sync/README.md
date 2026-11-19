# OneDrive → Firebase sin computadora encendida (integración **pendiente de activar**)

Este componente se ejecuta en GitHub Actions y lee **un único Excel XLSX desde Microsoft Graph**, usando un permiso delegado de solo lectura (`Files.Read`). No usa la API REST de Excel, porque esta no admite cuentas personales para ciertas funciones: descarga los bytes del libro XLSX mediante Microsoft Graph `/drives/{drive-id}/items/{item-id}/content` y los interpreta en memoria con `openpyxl`.

La información **no se imprime en logs, no se guarda en GitHub y no se incluye en GitHub Pages**. Solo se escribe, con autorización, en documentos privados `owners/{uid}/entries/{sha256('mirrors\n'+id)}` de Firestore, con tipo `mirrors`, que la PWA ya presenta en «Sincronización → Cambios de Excel recibidos». Nunca marca congelaciones ni inventario como confirmados. No modifica el Excel.

## Alternativa sin Azure ni Cevaxin: rclone gratuito

Para OneDrive **personal** puede utilizarse el software libre [rclone](https://rclone.org/onedrive/), que trae su propia aplicación OAuth compartida. No es necesario crear una aplicación nueva de Microsoft Entra ni usar una cuenta de Cevaxin. **Requiere un inicio de sesión interactivo con Microsoft una sola vez** y conceder los permisos de OneDrive a rclone. No mantiene ninguna computadora encendida ni ejecuta el capturador Windows después de la vinculación.

- Durante el consentimiento de rclone se debe configurar `access_scopes` con `Files.Read Files.Read.All offline_access`. Los permisos **por defecto de rclone incluyen escritura**, así que no aceptar la configuración por defecto si se desea acceso de solo lectura. Una cuenta Outlook personal autorizada puede conceder acceso a más archivos del OneDrive; este proceso solo invoca `rclone cat` sobre el XLSX indicado, pero Microsoft no restringe necesariamente el token a ese archivo.
- No poner tokens ni JSON de rclone en GitHub público, capturas, conversaciones o códigos fuente. Guardar el JSON de token exclusivamente como secreto **ONEDRIVE_RCLONE_TOKEN** de GitHub Actions.
- Variables necesarias en GitHub: `ONEDRIVE_ACCESS_METHOD=rclone`, `ONEDRIVE_DRIVE_ID` (ID de la cuenta de OneDrive), `ONEDRIVE_RELATIVE_PATH` (ruta relativa a la copia XLSX dentro del OneDrive).
- El flujo prepara el entorno con `RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive`, `RCLONE_CONFIG_ONEDRIVE_DRIVE_TYPE=personal`, `RCLONE_CONFIG_ONEDRIVE_DRIVE_ID`, y configura `RCLONE_ONEDRIVE_ACCESS_SCOPES` para lectura. El token ya autorizado debe proceder de una sesión que haya solicitado esos permisos de lectura.
- Las credenciales de Firebase/Google Cloud siguen siendo necesarias mediante federación de identidad, y hay que comprobar que esté disponible sin habilitar facturación. Un token renovado por Microsoft dentro de un ejecutor efímero puede requerir renovación del secreto de GitHub en el futuro.
- **Desactivado por defecto:** `MCA_ONEDRIVE_SYNC_ENABLED` no debe activarse hasta completar una prueba ficticia y verificar que las hojas y columnas corresponden con el Excel autorizado. Nunca activar un enlace de acceso público a información clínica.

## Cuenta confirmada: OneDrive personal (Outlook)

Para registrar la integración se necesita una aplicación en Microsoft Entra que admita **cuentas personales de Microsoft** (o cuentas de organizaciones y personales). Este acceso no se obtiene por estar conectado a Firebase ni por compartir el Excel. La cuenta Outlook debe conceder autorización mediante Microsoft OAuth 2.0, sin introducir su contraseña en la aplicación ni en GitHub.

**Alcance real del consentimiento:** el permiso delegado `Files.Read` puede autorizar lectura de los archivos de OneDrive de la cuenta, no exclusivamente del Excel seleccionado. El programa está diseñado para **descargar únicamente el archivo identificado por `ONEDRIVE_DRIVE_ID` y `ONEDRIVE_ITEM_ID`**; esos identificadores no reducen técnicamente los privilegios del token. Si el propietario no acepta ese alcance, no activar esta solución. Nunca solicitar vínculos públicos de un Excel clínico.

El registro de aplicaciones requiere acceso a Microsoft Entra (puede necesitar un inquilino/alta de Azure). **No contratar ni habilitar servicios de pago** para completar este paso; detener si se exige una suscripción o método de pago. Verificar antes de habilitar el workflow.

## Estado actual

**Seguro y desactivado.** El workflow no ejecuta ninguna lectura ni transmisión mientras `MCA_ONEDRIVE_SYNC_ENABLED` no sea `true`. No se ha autenticado una cuenta Microsoft ni probado el archivo real. No se han subido datos reales.

## Configuración pendiente, sin compartir credenciales por chat

1. Confirmar que el Excel se puede abrir mediante la cuenta de Microsoft que autorizará la sincronización. Basta **una** cuenta autorizada, aunque otras personas editen el archivo compartido. Confirmar que es realmente un XLSX compatible y que contiene las hojas `ALMACENAMIENTO DE ALICUOTAS` y/o `SALIDA DE MUESTRA` con encabezados en fila 3 y datos desde fila 4. Si se cambia el esquema, adaptar el mapeo antes de ejecutar.
2. Registrar una app Microsoft Entra para cuentas personales y/o trabajo, según corresponda, con permiso delegado **Files.Read** y `offline_access`; realizar consentimiento interactivo único y obtener un refresh token por un método seguro. Guardarlo exclusivamente en GitHub Actions Secrets `ONEDRIVE_REFRESH_TOKEN`. Guardar `ONEDRIVE_CLIENT_ID` como Variable y, si la app es confidencial, `ONEDRIVE_CLIENT_SECRET` como Secret. **No** escribir tokens en el código, logs, GitHub Pages o chat. Obtener `driveId` y `itemId` de Microsoft Graph con consentimiento y guardarlos como Variables `ONEDRIVE_DRIVE_ID` y `ONEDRIVE_ITEM_ID`.
3. Configurar en Google Cloud **Workload Identity Federation (WIF)** de GitHub, restringido al repositorio y a la rama `main`, con cuenta de servicio de permisos mínimos para Firestore. Variables `GCP_WIF_PROVIDER` y `GCP_SYNC_SERVICE_ACCOUNT`. No usar ni generar claves privadas de servicio. Esto requiere validar su disponibilidad sin habilitar facturación. Si la consola exige plan de pago, **detener el despliegue**.
4. Obtener el UID correcto del propietario de la app en Firebase Authentication y configurarlo como `FIREBASE_OWNER_UID` (Variable). Verificar que la regla de lectura de Firestore sigue privada.
5. Probar una **copia del Excel con filas ficticias** en modo de revisión y confirmar que las filas aparecen como espejos pendientes en celular y no como inventario. Solo entonces, y con autorización expresa para alojar los datos reales en Firebase, establecer `MCA_ONEDRIVE_AUTHORIZED=true` y `MCA_ONEDRIVE_SYNC_ENABLED=true` en GitHub Variables.

## Límites y cautelas

- GitHub Actions programado funciona con demora variable; se solicita cada **15 minutos**, no en tiempo real. GitHub puede retrasar/saltar ejecuciones y desactiva workflows programados en repositorios públicos inactivos tras 60 días. Por tanto, **no es apropiado para tareas clínicas urgentes**.
- El proceso evita duplicación si se edita la **misma fila**: IDs deterministas basados en Drive, libro, hoja y número de fila. **Insertar, ordenar o mover filas puede cambiar la identidad** y debe revisarse antes de su uso clínico. No se borran automáticamente datos si desaparecen filas.
- Escanea hojas concretas, no archivos ajenos. Las filas que ya existían al activar se sincronizarán: no activar sobre un libro real sin autorización del titular de los datos.
- Después de cambiar el token o permisos de Microsoft puede ser necesario volver a autorizar.
- El plan Spark impone límites de lecturas/escrituras; evitar ejecuciones excesivas y supervisar cuota.
- WIF/Graph/GitHub Actions requieren configuración externa. No existe sincronización activa hasta completar esos pasos y una prueba real.