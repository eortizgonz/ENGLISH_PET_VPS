# PET Quest V46.22 — Pedagogical Diagnostic Intelligence

## Objetivo
Transformar un porcentaje general (por ejemplo Listening 62%) en un diagnóstico por patrón de error y una acción correctiva inmediata.

## Patrones principales
- gist
- numbers
- times
- opinion
- corrected_information
- spelling
- detail
- inference
- cohesion
- pronunciation
- prepositions
- phrasal_verbs
- grammar
- vocabulary

## Regla de evidencia
PET Quest exige al menos 3 intentos reales de un patrón antes de declararlo como debilidad. Con menos datos muestra `evidencia insuficiente`.

## Flujo
1. El alumno responde actividades del Practice Bank.
2. Cada respuesta guarda skill + matriz B1 + `diagnostic_patterns` en `learning_events`.
3. `/api/practice-diagnostic` reconstruye el diagnóstico exclusivamente desde evidencia del usuario autenticado.
4. Se identifica el patrón con peor precisión entre aquellos con evidencia suficiente.
5. Se explica la causa pedagógica en lenguaje natural.
6. Se generan/seleccionan 10 ejercicios originales del banco etiquetados con ese mismo patrón.
7. Se registra cada respuesta correctiva y el resultado 0–10.
8. Se compara la precisión previa con la precisión de la sesión correctiva.

## Ejemplo esperado
Listening: 62%
- Gist: 89%
- Numbers: 42%
- Times: 38%
- Opinion: 71%
- Corrected information: 35%
- Spelling: 58%

Problema principal: detectas la primera información, pero no reconoces con suficiente consistencia cuando el hablante la corrige posteriormente.

Acción: generar 10 ejercicios de `corrected_information`.

## Nota
Es inteligencia pedagógica formativa basada en evidencia de uso de PET Quest; no equivale a una calificación oficial Cambridge.
