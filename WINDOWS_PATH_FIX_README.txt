PET QUEST V46.30 - CORRECCION WINDOWS PATH
==========================================

CAUSA CORREGIDA
La ejecucion reportada estaba dentro de una ruta muy larga. En esa ubicacion,
varios archivos superaban 260 caracteres y Windows devolvia 404/FileNotFoundError
aunque los archivos si estaban incluidos en el ZIP.

INSTALACION RECOMENDADA
1. Extrae ESTE ZIP directamente en C:\\PET_RELEASE (o en el Escritorio).
2. Dentro veras una carpeta corta llamada PET.
3. Ejecuta PET\\START_PET_QUEST_POSTGRES_WINDOWS.bat
4. No renombres PET con un nombre largo ni la coloques dentro de muchas carpetas.

PostgreSQL esperado:
  Base: PET
  Usuario: postgres
  Puerto: 5432
  Password: la configurada para este entorno de desarrollo.

La aplicacion verifica automaticamente:
- longitud de ruta;
- existencia de todos los assets PWA;
- driver PostgreSQL;
- disponibilidad y esquema de la base PET.
