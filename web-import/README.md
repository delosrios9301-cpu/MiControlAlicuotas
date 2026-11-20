# Importación directa de Excel desde Android (sin capturador Windows)

Esta función permite **seleccionar un archivo XLSX** desde el selector de Android (incluido OneDrive si aparece como proveedor, o desde Descargas), leer su contenido **en el navegador** y almacenarlo como **capturas locales para revisión**.

- Se reconocen las hojas `ALMACENAMIENTO DE ALICUOTAS` (columnas B:X, desde fila 4) y `SALIDA DE MUESTRA` (columnas A:M, desde fila 4).
- Se leen las filas ya existentes en el Excel, además de las nuevas; no es necesario empezar con un archivo vacío.
- Volver a seleccionar el mismo libro actualiza las filas modificadas, conserva revisiones previas y evita recrear capturas de filas sin cambios.
- Las filas con identidad alterada o reordenadas se omiten y se cuentan como bloqueadas para revisión, evitando sobrescribir la captura de otra muestra.
- Los archivos nunca se adjuntan a GitHub ni se transmiten a servicios externos durante esta lectura. En la base local IndexedDB se conservan las capturas, sin valores anteriores en historial.
- Ninguna fila de Excel se marca automáticamente como procesada, congelada ni disponible. La revisión manual incorpora capturas completas como registros **pendientes**, que solo luego podrán sincronizarse mediante Firebase si las reglas y cuenta están verificadas.
- No se eliminan registros ni se reescribe el Excel. La importación no sustituye al libro original ni a la conexión automática OneDrive → Firebase (todavía pendiente de activar).

## Uso desde el teléfono
1. Abre **Mi Excel** en la aplicación.
2. Pulsa **Seleccionar Excel para importar**.
3. Elige una copia XLSX guardada en Descargas o el archivo desde OneDrive si aparece en el selector de Android.
4. Acepta la lectura local. El sistema mostrará el total de capturas nuevas, actualizadas, sin cambios o bloqueadas.
5. Abre **Capturas Excel para revisar** en Sincronización y revisa cada alícuota. Solo incorpora filas completas y comprobadas; las salidas no se crean como nuevas alícuotas.

Para ver cambios posteriores en el XLSX desde el teléfono, **debes volver a seleccionar el archivo actualizado**. Un vínculo privado guardado en Mi Excel no concede autorización OAuth para que la aplicación lo consulte automáticamente en segundo plano.

## Compatibilidad
Compatible con XLSX Office Open XML estándar de hasta 15 MB y 20 000 filas, con hojas y columnas especificadas. Algunos archivos protegidos, macros XLSM, cifrados o esquemas diferentes requerirán adaptación; no se asume que los datos clínicos reales coincidan con el modelo hasta probar una copia autorizada.
