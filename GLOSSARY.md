# Glossary (Repo Excerpt)

For the full glossary, see: https://github.com/instance001/Whatisthisgithub/blob/main/GLOSSARY.md

This file contains only the glossary entries for this repository. Mapping tag legends and global notes live in the full glossary.

## historical-janet-school-exploratory-build
| Term | Alternate term(s) | Alt map | External map | Relation to existing terminology | What it is | What it is not | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Historical Janet school exploratory build | Janet school build | ~ | ~ | Early MCM curriculum sandbox | Early exploratory build for training and observing Janet as an MCM-v0.1 student through tiny school-style lessons, organ prompts, telemetry, and remedial loops | Not a polished product repo; not a generic chatbot app | historical-janet-school-exploratory-build/janet.py; historical-janet-school-exploratory-build/telemetry_log.md |
| Janet organs | error_metabolism, reasoner, planner, checker, memory_router | ~ | ~ | Prompt-specialized module templates | Set of text-template organs loaded from `organs/` and wrapped as callable prompt modules over Janet's backend | Not biological organs; not proof of model cognition; not separate models with independent memory stores | historical-janet-school-exploratory-build/janet.py |
| School day | run_school_day | = | ~ | Curriculum playback harness | CLI harness that loads lessons for a grade and feeds them into Janet as concept-learning episodes | Not a classroom UI; not an autonomous curriculum generator | historical-janet-school-exploratory-build/run_school_day.py |
| Janet telemetry | telemetry log | = | ~ | Transparent health-tracking layer | Heuristic telemetry built from episodes to compute concept stats, spiral scores, coherence, stability, and organ-health estimates | Not a formal benchmark; not hidden model introspection | historical-janet-school-exploratory-build/telemetry_engine.py; historical-janet-school-exploratory-build/telemetry_log.md |
| Remedial plan | remediation plan | ~ | ~ | Threshold-based follow-up plan | Generated plan that reviews organ health against a threshold and recommends whether Grade 0-0.5 remediation is needed | Not a clinical intervention; not proof of broad competence | historical-janet-school-exploratory-build/remedial_plan.md |
| Miss DeepSeek teacher | Miss GPT, teacher_miss_gpt | ~ | ~ | Curriculum-generation teacher harness | Teacher-side script that asks a backend to produce Grade 0 or 0.5 JSONL lessons for Janet's curriculum | Not the student runtime; not a grading engine | historical-janet-school-exploratory-build/teacher_miss_gpt.py |
