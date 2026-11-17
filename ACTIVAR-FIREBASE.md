# Activación final de Firebase — Mi Control de Alícuotas

Proyecto exclusivo: **mi-control-de-alicuotas-cde8d**. Plan exigido: **Spark** (sin facturación). Web de GitHub Pages: https://delosrios9301-cpu.github.io/MiControlAlicuotas/

## Qué ya prepara este repositorio

- La aplicación está alojada en GitHub Pages; el ZIP y el capturador local de Excel NO se distribuyen desde este repositorio.
- Las reglas privadas están versionadas en [firebase/firestore.rules](firebase/firestore.rules). Permiten solo al UID autenticado acceder a `owners/<UID>/entries/<ID>`; incluyen el tipo `mirrors` de capturas autorizadas.
- En cada despliegue GitHub intenta leer la configuración PÚBLICA de Firebase Hosting (`/__/firebase/init.json`) para colocar automáticamente su `apiKey` pública en la aplicación. Si no existe, la web continúa en modo local y muestra el formulario «Conectar proyecto Firebase» en **Sincronización**.
- Alternativa para configurar la apiKey en todos los dispositivos: crear en GitHub, Settings > Secrets and variables > Actions > Variables, la variable pública **FIREBASE_WEB_API_KEY**. No es una contraseña ni clave de servicio. Vuelve a ejecutar «Publicar Mi Control de Alícuotas» tras guardarla.

## Lo que debe activar el propietario una sola vez en Firebase Console

1. [Authentication](https://console.firebase.google.com/project/mi-control-de-alicuotas-cde8d/authentication): **Sign-in method** > habilita **Correo electrónico/Contraseña** y guarda. Elige una contraseña exclusiva para esta app. No envíes contraseñas a ChatGPT.
2. [Firestore Database](https://console.firebase.google.com/project/mi-control-de-alicuotas-cde8d/firestore): crea la base **(default)** en modo **producción** si todavía no existe; en **Reglas** pega el contenido COMPLETO de [firebase/firestore.rules](firebase/firestore.rules) y pulsa **Publicar**. No uses «modo de prueba» ni reglas abiertas. Esto **no ocurre** al publicar GitHub Pages.
3. [Configuración del proyecto](https://console.firebase.google.com/project/mi-control-de-alicuotas-cde8d/settings/general): en **Tus aplicaciones**, registra una **aplicación web** en ese proyecto si no existe; conserva su **apiKey WEB pública**. El proyecto debe seguir siendo Spark. Si Firebase Hosting fue habilitado y vinculado al mismo sitio, GitHub Pages puede obtener automáticamente `/__/firebase/init.json`; si no, coloca la apiKey pública en el formulario **Sincronización > Conectar proyecto Firebase** de cada navegador, o en la variable pública de GitHub antes indicada.

**No compartas** JSON de cuenta de servicio, claves privadas, tokens, contraseñas ni datos clínicos.

## Prueba de punta a punta (sin pacientes reales)

1. En PC Windows, descomprime el paquete de conector entregado por ChatGPT en una carpeta LOCAL. Abre el libro de Excel autorizado y ejecuta `INICIAR-CON-EXCEL.bat`. Elige ese archivo. Instala Python 3 y `pywin32` si se solicita.
2. Desde `http://127.0.0.1:8765/` entra en **Sincronización**, introduce la configuración pública si corresponde e inicia sesión en Firebase. Confirma que el capturador está conectado. Activa el envío de Excel **solo si tienes autorización** para transferir esa información a Firebase.
3. Haz una modificación con **datos totalmente ficticios** en una de las hojas vigiladas, confirma la celda, revisa la captura en la PC y su sincronización.
4. En el teléfono abre https://delosrios9301-cpu.github.io/MiControlAlicuotas/ e inicia sesión con la misma cuenta. En **Sincronización** revisa las filas recibidas desde Firebase.
5. Desconecta temporalmente Internet de la PC, modifica otra fila ficticia y luego reconecta. Verifica que la cola se envíe al reabrir la aplicación local y que el cambio aparezca en Android.

**Limitaciones:** no se observan caracteres antes de confirmar una celda. La PC, Excel y el capturador deben estar activos. Los cambios se envían cuando la aplicación local está abierta. No hay garantía de tiempo real estricto con la PWA suspendida. Capturar una fila no confirma la congelación física.

## Verificación pendiente

GitHub Pages solo distribuye el sitio; **no concede permisos de administrador de Firebase**. Este repositorio no puede afirmar que Authentication, Firestore o las reglas estén activados hasta verificarlos contra el proyecto real. Conservar datos locales y no introducir registros clínicos reales mientras esté pendiente.
