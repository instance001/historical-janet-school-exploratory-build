# Historical Janet School — Exploratory Build

This repository is a historical archive of an early toy build exploring whether abstract reasoning can be observed inside output that might otherwise be dismissed as “junk” or low-value model behaviour.

The project used a human-facing, special-education-style school curriculum as the framing device. Within that frame, a large language model acted as the teacher, while a modest cognition model acted as the student. The system generated runs, logged telemetry, and preserved outputs for later inspection and assessment.

This repository is not an active project and is not expected to receive further development.

## Purpose

The purpose of this build was exploratory.

It investigated whether apparently noisy, failed, strange, repetitive, or low-quality model outputs could still contain meaningful traces of reasoning, abstraction, adaptation, or curriculum-following behaviour.

Rather than treating “junk” output as automatically useless, the project treated it as a possible site of weak signal: something to be logged, reviewed, and interpreted in context.

## Concept

The experiment was structured around a teacher/student interaction:

- **Teacher:** a large language model presenting curriculum-like tasks, prompts, guidance, or feedback.
- **Student:** a modest cognition model responding within the learning environment.
- **Curriculum frame:** a human-facing special-needs school curriculum, used as a structured and interpretable scaffolding device.
- **Telemetry:** run data and interaction traces logged for later review.
- **Assessment:** outputs examined for signs of reasoning, abstraction, failure modes, and behavioural patterns.

### Ethical note on curriculum framing

This project used a special-education-style curriculum as a structural device, not as a derogatory comparison or as a claim about real students, disability, or human cognition.

The framing was chosen because this kind of curriculum is often designed around cognitive gaps, staged progression, repetition, scaffolding, partial understanding, and careful observation of small gains. Those qualities made it useful for probing a modest cognition model beginning from minimal prior task competence.

The work concerns artificial model behaviour only. It should not be used to draw conclusions about real students, special-needs education, disability, clinical assessment, or educational practice.

Because of this curriculum framing, the repository should be interpreted carefully, respectfully, and within the spirit of the original intention.

## Repository status

This is a historical repository.

It contains materials from the initial exploratory build and run outputs. It is preserved as a record of the experiment rather than maintained as production software.

Expect the contents to be incomplete, rough, experimental, and possibly inconsistent.

## How to read this repository

This repository is best understood as an artifact of an early investigation, not as a polished framework.

When reviewing the outputs, useful questions include:

- Does the student model appear to follow curriculum structure?
- Are there recurring patterns in apparently low-quality output?
- Can abstract reasoning be inferred from partial, malformed, or noisy responses?
- Where does the model fail, and are those failures systematic?
- Does the teacher/student framing expose behaviours that would be missed in ordinary prompt/response evaluation?
- What does the telemetry suggest about interaction patterns over time?

## What this is not

This repository is not:

- an active application
- a maintained educational tool
- a validated cognitive assessment system
- a special education curriculum
- a claim about human learning or disability
- a production-ready model evaluation framework

It should be read as an exploratory prototype and historical record.

## License

This project is licensed under the **GNU Affero General Public License v3.0**.

See the [`LICENSE`](LICENSE) file for the full license text.

SPDX license identifier:

```text
AGPL-3.0-only
