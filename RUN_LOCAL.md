# PET Quest V46.6 MASTER — ejecución local

## Windows
1. Descomprime el ZIP.
2. Verifica que Python 3 esté instalado (`python --version`).
3. Ejecuta `START_PET_QUEST_WINDOWS.bat` (redirige al launcher PostgreSQL seguro).
4. Abre `http://127.0.0.1:8080` si el navegador no se abre automáticamente.

Usuarios demo (solo desarrollo local):
- student@petquest.local / Student123!
- teacher@petquest.local / Teacher123!
- school@petquest.local / School123!
- admin@petquest.local / Admin123!

## macOS / Linux
```bash
chmod +x start_pet_quest.sh
./start_pet_quest.sh
```

## Docker local
```bash
docker compose -f docker-compose.local.yml up --build
```
Abrir `http://127.0.0.1:8080`.

## Verificación
```bash
python qa_master_v46_5.py
```

En V46.30 local, la identidad/autenticación usa PostgreSQL `PET.pet_users`; el historial académico, sesiones y evidencias educativas permanecen en SQLite de forma deliberada. El launcher valida ambos almacenes antes de abrir la aplicación.
