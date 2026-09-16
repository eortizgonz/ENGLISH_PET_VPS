# PET Quest V46.27 - PET Mastery Orchestrator

## Student architecture

1. PET Learn: 100 original micro-lessons from A2 to B1+.
2. PET Practice: existing large profile-aware banks (5,000 For Schools / 3,000 Adult) with B1 Matrix metadata and remediation.
3. PET Exam: 20 complete original Full Mocks per profile.
4. PET Error DNA: evidence-backed error map and targeted 10-item remediation.
5. PET AI Tutor: explain -> guided practice -> correction -> recheck -> targeted practice loop.
6. PET Readiness: Reading, Writing, Listening, Speaking and Overall readiness. Pass probability stays OFF until the calibration service enables it.

## Mastery goals

- pass: minimum formative target 60% in each skill.
- solid: Reading/Listening 75%, Writing/Speaking 70%.
- excellent: Reading >=85%, Listening >=85%, Writing >=80% (=16/20), Speaking >=80% (=4/5) plus three recent Speaking attempts >=80%.
- b2: Reading/Listening >=90%, Writing/Speaking >=85%, PET Learn B1+ complete, and at least 10 B2 bridge practice responses with >=80% accuracy.

The orchestrator does not automatically promote the learner to a Full Mock until the selected goal gate is met. Existing manual exam access is preserved for teachers/testing workflows.

## Dashboard

The home dashboard combines readiness, skill risk, error counts, corrected/pending/recurrent targets, next objective, exam date, minutes studied today, mastery goal, probability-calibration status and one primary CTA: CONTINUAR MI ENTRENAMIENTO.

## Scientific boundary

Readiness is a formative PET Quest score. Estimated pass probability appears only when the existing psychometric calibration endpoint reports `probability_enabled=true`. No probability is fabricated when calibration is provisional.
