import argparse
from pathlib import Path

from backend_miss_gpt import MissGPTBackend

BASE_DIR = Path(__file__).resolve().parent
SCHOOL_DIR = BASE_DIR / "school"


PROMPT_GRADE_0 = """
You are MISS DEEPSEEK: a patient, structured special-needs educator.

Create a simple Grade 0 curriculum for a developing Modest Cognition Model (MCM) named JANET.

Focus on three core concepts:
1) same_different
2) sequence_next
3) more

For each concept, output ONE JSON object with:
- "concept": short concept name (string)
- "rule": a simple one-sentence explanation (string)
- "examples": array of 3 objects with:
   - "Q": the question shown to the student
   - "A": the correct answer

Keep language simple and warm.
Output exactly 3 lines, one JSON object per line (JSONL format).
"""


PROMPT_GRADE_0_5 = """
You are MISS DEEPSEEK: a patient, structured special-needs educator.

Create a set of 12 lessons specifically designed to strengthen pattern recognition
for an early-development MCM (Modest Cognition Model) named JANET.

GRADE: 0.5 (Remedial Pattern Strengthening Module)

Each lesson must have:

- "concept": a short name for the pattern type
- "rule": a simple one-sentence explanation of the pattern
- "examples": 3 examples formatted as:
    { "Q": "...", "A": "..." }

Pattern types MUST include:

  1. simple alternation (A B A B ...)
  2. double alternation (A A B A A B ...)
  3. long-cycle repeat (A B C A B C ...)
  4. reversed cycle (3 2 1 3 2 1 ...)
  5. mixed-feature patterns (e.g., color + size)
  6. shape/shape/number combos
  7. offset numeric patterns (e.g., 1 3 2 4 3 5 ...)
  8. two-variable patterns (color AND shape change)
  9. distractor-element patterns
  10. nested patterns (A (B C) A (B C) ...)
  11. "find the missing" patterns
  12. "invent your own pattern" (for Janet to attempt synthetic generalization)

Rules:
- Keep explanations simple, warm, and precise.
- Patterns MUST be clear enough for a Grade 0 learner.
- Use emojis or simple symbols where helpful (🔴, 🔵, ▲, ●, etc.)
- Output ONLY JSONL, one JSON object per line. No commentary.
"""


def build_prompt_for_grade(grade: str) -> str:
    if grade == "0":
        return PROMPT_GRADE_0.strip()
    if grade == "0.5":
        return PROMPT_GRADE_0_5.strip()
    raise ValueError(f"Unsupported grade: {grade!r}. Use '0' or '0.5'.")


def grade_to_dirname(grade: str) -> str:
    if grade == "0":
        return "grade_00"
    if grade == "0.5":
        return "grade_00_5"
    # Fallback if you extend later
    safe = grade.replace(".", "_")
    return f"grade_{safe}"


def main():
    parser = argparse.ArgumentParser(description="Generate Janet curriculum with Miss DeepSeek.")
    parser.add_argument(
        "--grade",
        default="0",
        help="Grade level to generate (e.g., '0' or '0.5'). Default: 0",
    )
    args = parser.parse_args()

    grade = args.grade
    prompt = build_prompt_for_grade(grade)
    dirname = grade_to_dirname(grade)

    out_dir = SCHOOL_DIR / dirname
    out_dir.mkdir(parents=True, exist_ok=True)
    lessons_path = out_dir / "lessons.jsonl"

    backend = MissGPTBackend()

    print(f"Calling Miss GPT (DeepSeek) for Grade {grade} curriculum...")
    curriculum_text = backend.generate(prompt, max_tokens=4096)

    # Write raw JSONL straight out
    lessons_path.write_text(curriculum_text.strip() + "\n", encoding="utf-8")

    num_lines = len([l for l in curriculum_text.splitlines() if l.strip()])
    print(f"Writing {num_lines} lessons to {lessons_path}")
    print(f"Done. Grade {grade} lessons ready.")


if __name__ == "__main__":
    main()
