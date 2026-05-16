import argparse
import json
from pathlib import Path

from janet import Janet

BASE_DIR = Path(__file__).resolve().parent
SCHOOL_DIR = BASE_DIR / "school"


def grade_to_dirname(grade: str) -> str:
    if grade == "0":
        return "grade_00"
    if grade == "0.5":
        return "grade_00_5"
    safe = grade.replace(".", "_")
    return f"grade_{safe}"


def load_lessons_for_grade(grade: str):
    dirname = grade_to_dirname(grade)
    lessons_path = SCHOOL_DIR / dirname / "lessons.jsonl"
    if not lessons_path.exists():
        raise FileNotFoundError(f"No lessons file found for grade {grade} at {lessons_path}")

    lessons = []
    with lessons_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                lessons.append(obj)
            except json.JSONDecodeError:
                # Skip malformed lines quietly
                continue
    return lessons, lessons_path


def main():
    parser = argparse.ArgumentParser(description="Run a Janet school day for a given grade.")
    parser.add_argument(
        "--grade",
        default="0",
        help="Grade level to run (e.g., '0' or '0.5'). Default: 0",
    )
    args = parser.parse_args()
    grade = args.grade

    lessons, path = load_lessons_for_grade(grade)
    print(f"Starting Janet Grade {grade} school day...")
    print(f"Loaded {len(lessons)} lessons from {path}.\n")

    janet = Janet()
    # Track grade in her state
    janet.state["grade"] = grade

    for idx, lesson in enumerate(lessons, start=1):
        concept = lesson.get("concept", f"concept_{idx}")
        rule = lesson.get("rule", "")
        examples = lesson.get("examples", [])

        lesson_block = {
            "concept": concept,
            "grade": grade,
            "explanation": rule,
            "examples": examples,
        }

        print(f"=== Teaching concept: {concept} ===")
        resp = janet.learn_concept(concept, lesson_block)
        print("Janet's restatement of the rule:")
        print(resp)
        print("-" * 40)
        print()

    print(f"Grade {grade} school day complete. Check memory/ and logs/ for details.")


if __name__ == "__main__":
    main()
