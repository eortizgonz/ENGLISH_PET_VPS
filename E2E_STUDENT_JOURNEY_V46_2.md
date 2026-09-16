# PET Quest V46.2 — End-to-End Student Journey

## Defects found and fixed
1. Assignment UI considered `{done:false}` completed because it tested object existence. Fixed to read the actual `done` flag.
2. Starting an assignment did not have a reliable completion transition. The active assignment is now closed only when its learning session completes.
3. Level 3 `Subir nivel` capped at level 3 and could loop indefinitely. Level 3 now ends in a terminal course-complete screen.
4. Speaking now records session completion after Part 4.
5. Writing now requires evidence from both practice parts and then offers an explicit finish action.

## End-to-end QA
`qa_student_end_to_end_v46_2.py` validates:
- syntax of all application JavaScript files;
- every generated clickable data-action has a handler;
- Reading and Listening items are selectable and have valid answers;
- levels 1, 2 and 3 exist;
- final-level terminal state and course-completion persistence;
- assignment start/completion semantics;
- Writing and Speaking finalization;
- V41/V43/V44/V46 academic/release regressions;
- isolated backend startup;
- real student login;
- synchronization and readback of a completed learning journey snapshot.

Note: Chromium in this execution environment is policy-blocked from opening local IP/localhost URLs, so visual browser clicking could not be executed here. Click coverage was instead checked against real DOM action selectors/handlers, and application state/API flows were exercised deterministically.
