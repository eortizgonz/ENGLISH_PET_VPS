# QA PostgreSQL Master Content — PET Quest V46.30

## Objetivo
Corregir la instalación en la que PostgreSQL contenía las tablas operativas pero el material pedagógico seguía residiendo únicamente en JSON/archivos.

## Resultado
- PostgreSQL schema: 49 tablas declaradas.
- Nuevas tablas maestras: 7.
- Practice Bank For Schools: 5,000 ítems.
- Practice Bank Adult: 3,000 ítems.
- PET Learn curriculum: 100 lecciones.
- Full Mocks: 40 packs.
- Exam items: 2,500 (Reading 1,280; Listening 1,000; Writing 80; Speaking 140).
- Audio assets inventariados: 877.
- School Audio Bank: 500/500 rutas presentes.

## Tablas maestras cargadas al instalar
- content_packages
- practice_bank_items
- curriculum_lessons
- audio_assets
- exam_packs
- exam_items
- content_seed_runs

## Runtime DB-first
Los siguientes módulos consultan PostgreSQL primero y conservan JSON como fallback offline:
- Practice Bank
- Practice Diagnostic
- Audio Bank
- Full Mock Bank
- Mock Listening
- Full Mock Mastery
- PET Learn Curriculum

## Tablas que pueden iniciar vacías correctamente
Eventos, sesiones, errores de estudiante, intentos de mock, speaking, auditoría y tablas escolares/administrativas se llenan con uso real o configuración del colegio. No se insertan datos ficticios.

## Audio
Los binarios permanecen en assets/audio. PostgreSQL almacena ruta, SHA-256, transcript, pregunta, opciones, respuesta y metadata técnica. Esto evita inflar innecesariamente la base con BLOBs y mantiene streaming eficiente.

## Pruebas ejecutadas
- qa_master_content_postgres_v46_30.py: 40/40 PASS
- qa_windows_safe_login_v46_30.py: 27/27 PASS
- qa_audio_bank_v46_18.py: 28/28 PASS
- qa_full_mock_20_v46_20.py: 272/272 PASS
- qa_registration_recovery_v46_30.py: PASS
- verify_windows_runtime.py: 165/165 recursos PASS

## Limitación de validación
Este entorno no dispone de un servidor PostgreSQL ejecutándose. El DDL y el cargador fueron validados estáticamente y contra los archivos fuente reales. En Windows, setup_postgres_pet.py ejecuta schema + seed y postgres_check.py verifica la presencia y los conteos reales antes de permitir /api/ready.
