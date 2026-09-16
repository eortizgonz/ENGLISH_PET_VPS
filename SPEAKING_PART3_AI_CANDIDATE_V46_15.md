# PET Quest V46.15 — Speaking Part 3 AI Candidate

## Objetivo
Añade una conversación formativa por turnos para Speaking Part 3. El candidato simulado propone, responde, introduce alternativas, pide comparación y conduce a una decisión final.

## Funciones evaluadas
- suggestion
- agreement
- disagreement
- justification
- turn-taking
- negotiation
- final decision

Cada función queda registrada por turno y agregada por sesión. La puntuación `Interactive Communication` es automática y formativa; no es una calificación oficial de Cambridge.

## Persistencia
- `speaking_interaction_sessions`: una fila por conversación y usuario.
- `speaking_interaction_turns`: una fila por turno, enlazada a la sesión.
- `speaking_attempts`: recibe evidencia Part 3 para el cálculo de preparación individual.

## Privacidad
Las sesiones están vinculadas al `student_id` autenticado y el ciclo de eliminación de privacidad purga las sesiones y sus turnos por cascada.

## Validación
- Part 3 AI Candidate QA: 24/24 PASS
- Speaking AI Examiner regression: 40/40 PASS
- Student E2E: 77/77 PASS
- Academic regression: 20/20 PASS
- Full persistence: 45/45 PASS
- User isolation: 11/11 PASS
- Security: 8/8 PASS
- Startup: 9/9 PASS
- Screen integrity: 184/184 PASS
