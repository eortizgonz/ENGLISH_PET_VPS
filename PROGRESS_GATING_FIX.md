# Progress gating fix

This revision makes guided Reading/Listening practice resumable per user and blocks progression until the current exercise is answered correctly.

Behavior:
- Every check attempt is appended to `data.history` and persisted immediately through `/api/snapshot`.
- A wrong answer stays on the same exercise. The correct option is no longer revealed automatically.
- The learner can change the answer and retry.
- `Siguiente` is enabled only when the current answer is correct; the handler also validates this rule defensively.
- When a skill/level is opened again, normal practice starts at the first question that has no correct practice attempt in the persisted history.
- Correctly completed practice questions are therefore not forced on the learner again after reload/login.
- Previous attempts remain visible in the existing answers/history screen.
- Mock-exam attempts do not mark guided-practice exercises as completed.

The persistence remains user-scoped through the existing snapshot stored for `users.id`.
