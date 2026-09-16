# PET Quest V46.28 — Item-by-item Audit Gate

Mocks A/B/C were audited element by element: 96 Reading + 75 Listening + 6 Writing + 12 Speaking = 189 audit cards. Any `REJECTED_FOR_REVISION` element blocks productive activation of that mock. See `THREE_MOCK_ITEM_AUDIT_V46_28.md`, `.json`, `.csv` and `VALIDATION_ITEM_BY_ITEM_AUDIT_V46_28.txt`. Internal reviewer passes are automated; external academic signoff remains pending.

# PET Quest V46.27 - PET Mastery Orchestrator

This release adds the student mastery dashboard and orchestrates PET Learn, Practice, Exam, Error DNA, AI Tutor and gated Readiness goals.

# PET Quest V46.26 — Dual Profile Adult + For Schools

**New in V46.26:** two explicit B1 content profiles. `B1 Preliminary for Schools` preserves the school-age route; `B1 Preliminary – Adult` adds 20 adult-context Full Mocks, 3,000 adult Practice Bank activities, 300 adult mock audio recordings, profile-aware diagnostics and per-user profile persistence. See `ADULT_PROFILE_V46_26.md`.


**Current MASTER.** V46.25 hardens per-user local persistence, progress refresh, Writing draft saving, UI action addressability and full technical validation of the 500-audio PET Audio Bank. Synthetic audio is not represented as human studio audio.

# PET Quest V46.24 — Error DNA™ Validated

> V46.24 añade Error DNA™: mapa individual por Grammar, Listening, Reading, Writing y Speaking, con estados basados en evidencia real y acceso directo a remediación de 10 ejercicios.

# PET Quest V46.23 — Child Learning Experience 100

Current MASTER. Adds a complete 9–14 child learning journey on top of V46.22: APRENDER → PRACTICAR → DOMINAR → SIMULAR, age-adapted micro-goals, prominent “No entiendo”, optional breaks, mood check-in, mastery-based rewards, diagnostic-to-10-item remediation, per-user local state and server event tracing.

Important evidence boundary: **100/100 means the internal functional child-UX contract is implemented and machine-validated. It is not an external usability study with real children or an external academic sign-off.**

See `CHILD_LEARNING_EXPERIENCE_V46_23.md` and `VALIDATION_CHILD_EXPERIENCE_V46_23.txt`.

---

# PET Quest V46.22 — Practice Bank 5,000 + B1 Diagnostic Matrix

Nueva MASTER: banco de 5.000 actividades separado de Full Mocks, seis niveles CEFR, 13 competencias, metadata diagnóstica completa por ítem y adaptación por debilidades.

## V46.20 - PET Mastery 20 Full Mocks

20 complete forms (A-T): 640 Reading questions, 500 Listening questions, 40 Writing tasks, and 80 Speaking parts. Structural/content complete; external academic sign-off and psychometric form equivalence remain pending.

# PET Quest V46.19 — PET Audio Bank 500

**Current MASTER.** Adds 500 new Listening training recordings, four training speeds and strict two-play Exam Mode. See `PET_AUDIO_BANK_V46_18.md`.

# PET Quest V46.17 — Anonymous Cambridge Scale Calibration

V46.17 adds an anonymous external-outcomes cohort for PET Quest Readiness ↔ Cambridge English Scale calibration. It tracks minimum (300), robust (500) and mature (1,000+) evidence targets, enforces distribution across Fail/A2, B1 Pass, B1 Grade B/Merit and B2 Grade A/Distinction performance, uses a subject-level holdout, and keeps scale equivalence OFF until holdout-quality gates and an independent psychometric review pass.

# PET Quest V46.15 — Part 3 AI Candidate

V46.15 añade conversación real por turnos para Speaking Part 3 con candidato IA simulado y registro por usuario de suggestion, agreement, disagreement, justification, turn-taking, negotiation y final decision. Ver `SPEAKING_PART3_AI_CANDIDATE_V46_15.md`.

# PET Quest V46.14 - Speaking AI Examiner + Writing Mastery + Full Function Voice Simulation Validated

V46.14 inherits V46.13 and adds a per-user Speaking AI Examiner with microphone recording, live acoustic capture, transcript analysis, fluency/WPM/pause/hesitation/restart metrics, grammar/vocabulary/discourse analysis, pronunciation/intelligibility/stress/intonation proxies, interaction analysis, a five-criterion 0–5 practice rubric, local-device voice storage and backend persistence of metrics and results. The latest evidence per Speaking part feeds the individual preparation score.

See `SPEAKING_AI_EXAMINER_V46_14.md` and `VALIDATION_SPEAKING_V46_14.txt`. Automatic Speaking evaluation remains formative and is not an official Cambridge grade.

V46.13 inherits the V46.12 full-function, per-user persistence and multi-voice simulation release and adds a complete Writing improvement loop. Every Writing production now receives Content, Communicative Achievement, Organisation and Language scores from 0-5 (total 0-20), an explanation for every criterion, a gap-to-18 plan, four immediate corrective exercises and per-user remediation persistence. Re-evaluation is stored as a new attempt to show progression.

See `WRITING_MASTERY_V46_13.md` and `VALIDATION_WRITING_V46_13.txt`. The automated Writing score remains formative and is not an official Cambridge mark.

## Inherited V46.12 validation

V46.12 audits the V46.11 release end-to-end and strengthens three areas:

1. **Per-user state isolation**: the in-progress Full Mock Listening state is now namespaced by authenticated `user_id`, while completed attempts continue to persist in backend tables.
2. **Visible individual progress**: authenticated students see their PET Quest Preparation Score in the top bar on every screen; the full dashboard still shows errors, corrections, pending errors, four skills and exam-level results.
3. **Audio simulation**: all 45 Full Mock A/B/C recordings and all 15 V40.2 fidelity recordings were regenerated with distinct offline synthetic voice profiles and FFmpeg mastering at 48 kHz / 192 kbps mono, approx. -16 LUFS / -1.5 dBTP target. Dialogue recordings alternate voice profiles and include natural pauses.

The voices are **synthetic simulations**, not human studio recordings. `studio_audio_ready` and `external_academic_signoff` therefore remain false until independent human recording/review exists.

See `FULL_FUNCTION_AUDIT_V46_12.md`, `VOICE_SIMULATION_MANIFEST_V46_12.json` and `FIDELITY_VOICE_SIMULATION_MANIFEST_V46_12.json`.

## Mastery rule
An error pattern is marked mastered only after **at least three recent correct attempts**, matching the backend remediation rule.
## V46.16 — PET Readiness Calibration Lab
Adds leakage-safe train/holdout calibration against external outcomes, Brier/ECE/AUC/sensitivity/specificity gates, teacher-mock exclusion from scientific fitting, and an independent psychometric review gate. Pass probability remains OFF until every statistical and external-review gate passes. See `READINESS_CALIBRATION_V46_16.md`.


## V46.22 Pedagogical Diagnostic Intelligence
- Diagnóstico por patrón a partir de intentos reales del usuario.
- Evidencia mínima: 3 intentos por patrón antes de declarar una debilidad.
- Desglose de Listening por gist, numbers, times, opinion, corrected information, spelling y otros patrones.
- Problema principal explicado en lenguaje pedagógico.
- Generación inmediata de 10 ejercicios correctivos del patrón más débil.
- Medición antes/después y persistencia en learning_events por usuario.


## Error DNA™ V46.24

Mapa individual de error por Grammar, Listening, Reading, Writing y Speaking. Usa evidencia persistida, exige evidencia mínima antes de colorear un patrón y permite abrir un plan correctivo de 10 ejercicios desde el nodo prioritario. Ver `ERROR_DNA_V46_24.md` y `VALIDATION_ERROR_DNA_V46_24.txt`.