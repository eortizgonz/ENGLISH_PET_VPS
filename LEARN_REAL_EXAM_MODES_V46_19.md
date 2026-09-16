# PET Quest V46.19 — LEARN MODE vs REAL EXAM MODE

## Objetivo
Separar claramente el entrenamiento auditivo de la simulación estricta.

### ♾️ LEARN MODE
- Reproducciones ilimitadas.
- Velocidades: 0.75x, 0.85x, 1.00x, 1.10x.
- Transcript disponible para revisión.
- Las escuchas no consumen reproducciones del modo examen.

### 🎓 REAL EXAM MODE
- Velocidad fija 1.00x.
- Exactamente dos reproducciones máximas por clip y sesión.
- Transcript oculto.
- Cada entrada desde LEARN MODE inicia una nueva sesión en 0/2.
- Tercera reproducción bloqueada.

## Persistencia
Estado local separado por usuario mediante `petquest_v4619_audio_bank_u_<user_id>`.
Los contadores `learnPlays` y `examPlays` son independientes.

## QA
- Learn/Real Exam V46.19: 16/16 PASS
- PET Audio Bank: 28/28 PASS
- Startup: 9/9 PASS
- Student E2E: 80/80 PASS
- User isolation: 11/11 PASS
