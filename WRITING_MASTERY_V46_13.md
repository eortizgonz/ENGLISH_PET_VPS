# PET Quest V46.13 - Writing Rubric & Automatic Remediation

V46.13 standardises the learner-facing Writing review around four 0-5 formative criteria:

- Content: 0-5
- Communicative Achievement: 0-5
- Organisation: 0-5
- Language: 0-5
- Total: 0-20

For every evaluated production PET Quest stores the original text, word count, task/part, the four criterion scores, criterion-by-criterion explanations, detected language errors, a target score of 18/20, four prioritised improvement areas and four generated corrective exercises.

## Improvement loop

1. Learner submits a production.
2. PET Quest returns the 0-20 formative rubric.
3. Each criterion receives an explicit explanation.
4. PET Quest calculates the gap to 18/20.
5. Four priority weaknesses/improvement areas are generated.
6. Four exercises appear immediately.
7. Every checked exercise is persisted through `/api/academic-remediation` with the authenticated student id.
8. The learner edits the original production and evaluates again.
9. The new Writing attempt is stored separately in the user's snapshot so score evolution can be measured.

Article and Story are alternatives for Writing Part 2. They are not counted as a third PET Writing task.

This is an automated formative assessment. It is not an official Cambridge mark and does not replace qualified human assessment where external academic validation is required.
