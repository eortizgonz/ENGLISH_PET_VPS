# PET Quest V46.16 — PET Readiness Calibration Lab

## Principle
PET Quest Readiness is a preparation index until external calibration is validated. The application must not publish a pass probability simply because it has a numeric readiness score.

## Scientific dataset
The validation model uses only `official_exam` and `external_mock` outcomes. `teacher_mock` records remain useful descriptively but are excluded from the scientific calibration sample. Only one latest external outcome per student is used to prevent repeated-student inflation and train/holdout leakage.

## Holdout design
Students are deterministically partitioned by student/exam identity into approximately 80% training and 20% holdout. The same student cannot appear in both groups.

## Publication gates
All gates must pass:
- >=300 unique students with external outcomes
- >=75 passes and >=75 fails
- >=50 holdout students
- holdout AUC >= 0.70
- holdout Brier <= 0.20
- holdout ECE <= 0.10
- sensitivity >=65%
- specificity >=65%
- independent psychometric review = approved

If any gate fails, `probability_enabled=false`.

## Metrics
The laboratory computes training and holdout AUC, Brier score, log loss, expected calibration error (ECE), classification accuracy, sensitivity, and specificity.

## External review
The new `psychometric_reviews` table stores reviewer, independent organization, credentials, decision, evidence reference, notes and timestamp. Software QA cannot self-approve this gate.

## API
- `GET /api/academic-calibration` — full lab report and gates.
- `POST /api/calibration/outcomes` — external outcome evidence.
- `POST /api/calibration/review` — independent review evidence, restricted to academic reviewer/admin roles.
- `GET /api/readiness/probability?readiness=...` — returns no probability while the release gate is OFF.

## Interpretation
Until the gate is fully validated, user-facing values remain PET Quest Preparation/Readiness indicators and must never be described as a scientifically validated probability of passing Cambridge.
