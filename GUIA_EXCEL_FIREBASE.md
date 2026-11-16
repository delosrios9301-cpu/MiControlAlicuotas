# Mi Control de Alícuotas — Excel Windows y Firebase
## Estado
GitHub Pages publica únicamente la interfaz web estática. La integración de Excel requiere el capturador local en Windows y Firebase Auth + Firestore configurados en el proyecto independiente `mi-control-de-alicuotas-cde8d` (Spark).

## Captura en Windows
Descomprimir el paquete **MiControlAlicuotas_ConectorExcel_Windows** fuera del repositorio, tener Excel de escritorio y Python 3, ejecutar `INICIAR-CON-EXCEL.bat` y seleccionar el libro. Se observan únicamente las hojas **ALMACENAMIENTO DE ALICUOTAS** (B-X) y **SALIDA DE MUESTRA** (A-M), desde la fila 4. Los cambios se capturan al confirmar celdas, no durante la escritura sin confirmar. La PC y Excel deben permanecer abiertos.

Las capturas originales se guardan en SQLite local, nunca se publican en GitHub Pages. Solo si se inicia sesión con la cuenta Firebase y se autoriza expresamente desde la PC, las nuevas modificaciones se transfieren como **copias de espejo** a una colección privada en Firestore. Incluyen datos potencialmente sensibles; no habilitar sin permiso del titular de los datos. El envío se puede detener en la misma pantalla.

## Firebase: lo que falta configurar
- Firebase Authentication > Email/Password.
- Firestore `(default)` en modo producción, reglas privadas de `firebase/firestore.rules` (este repositorio).
- Crear app web Firebase; copiar su **apiKey pública** en `firebase-config.js` de la web y del paquete Windows; `projectId` fijo. Nunca subir secretos o cuentas de servicio.
- Autorizar los dominios que sean necesarios para Authentication, incluido `delosrios9301-cpu.github.io`.
- Iniciar sesión con la **misma cuenta** en la aplicación local Windows y la web Android.

La sección **Sincronización** del teléfono muestra los cambios compartidos, sin tratarlos como congelaciones confirmadas. La actualización depende de conexión, navegador abierto y cuotas Spark; no es tiempo real estricto. No se garantiza funcionamiento sin configurar Firebase, y no se ha probado la transferencia real en el proyecto.
