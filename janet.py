import json
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend_chatty20b import Chatty20BBackend

# ---------- Paths ----------

BASE_DIR = Path(__file__).resolve().parent
ORGANS_DIR = BASE_DIR / "organs"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs" / "sessions"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ---------- Backend Interface ----------

class LLMBackend:
    """
    Abstract backend interface for Janet's organs.
    """
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        raise NotImplementedError


# ---------- Organ Wrapper ----------

class Organ:
    def __init__(self, name: str, template: str, backend: LLMBackend):
        self.name = name
        self.template = template.strip()
        self.backend = backend

    def __call__(
        self,
        message: str,
        state: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        max_tokens: int = 512,
    ) -> str:
        """
        Build a prompt: organ instructions + state + meta + input.
        """
        state = state or {}
        meta = meta or {}

        prompt_parts = [
            self.template,
            "",
            "[STATE]",
            json.dumps(state, ensure_ascii=False, indent=2),
            "",
            "[META]",
            json.dumps(meta, ensure_ascii=False, indent=2),
            "",
            "[INPUT]",
            message,
            "",
            "[OUTPUT]",
        ]
        prompt = "\n".join(prompt_parts)
        return self.backend.generate(prompt, max_tokens=max_tokens)


# ---------- Memory & Logging ----------

class MemoryStore:
    def __init__(self, concepts_path: Path, episodes_path: Path):
        self.concepts_path = concepts_path
        self.episodes_path = episodes_path

        # Ensure files exist
        for p in (self.concepts_path, self.episodes_path):
            if not p.exists():
                p.write_text("", encoding="utf-8")

    def append_episode(self, episode: Dict[str, Any]) -> None:
        line = json.dumps(episode, ensure_ascii=False)
        with self.episodes_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def store_concept(self, name: str, payload: Dict[str, Any]) -> None:
        record = {
            "concept": name,
            "data": payload,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
        }
        line = json.dumps(record, ensure_ascii=False)
        with self.concepts_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


# ---------- Janet (Student) ----------

class Janet:
    def __init__(self, backend: Optional[LLMBackend] = None):
        # Default backend is Chatty-20B if none provided
        self.backend = backend or Chatty20BBackend()
        self.organs = self._load_organs()
        self.memory = MemoryStore(
            concepts_path=MEMORY_DIR / "concepts.jsonl",
            episodes_path=MEMORY_DIR / "episodes.jsonl",
        )
        self.state: Dict[str, Any] = {
            "grade": 0,
            "concepts_mastered": [],
        }

    def _load_organs(self) -> Dict[str, Organ]:
        organ_files = {
            "error_metabolism": "error_metabolism.txt",
            "reasoner": "reasoner.txt",
            "planner": "planner.txt",
            "checker": "checker.txt",
            "memory_router": "memory_router.txt",
        }
        organs: Dict[str, Organ] = {}
        for key, filename in organ_files.items():
            path = ORGANS_DIR / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing organ file: {path}")
            template = path.read_text(encoding="utf-8")
            organs[key] = Organ(key, template, self.backend)
        return organs

    def log(
        self,
        role: str,
        input_text: str,
        output_text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        episode = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "role": role,
            "input": input_text,
            "output": output_text,
            "meta": meta or {},
            "state_snapshot": self.state.copy(),
        }
        self.memory.append_episode(episode)

    # ----- Core thinking entrypoint -----

    def think_with_organ(
        self,
        organ_name: str,
        message: str,
        meta: Optional[Dict[str, Any]] = None,
        max_tokens: int = 512,
    ) -> str:
        organ = self.organs[organ_name]
        response = organ(
            message=message,
            state=self.state,
            meta=meta,
            max_tokens=max_tokens,
        )
        self.log(
            role=organ_name,
            input_text=message,
            output_text=response,
            meta=meta,
        )
        return response

    # ----- High-level behaviors -----

    def answer_question(self, question: str) -> str:
        """
        Main “student answering” path:
        1) Try error metabolism (honesty about not knowing)
        2) If she attempts an answer, run through reasoner
        """
        # First pass: error metabolism organ decides if she "knows" or needs teaching.
        em_resp = self.think_with_organ(
            "error_metabolism",
            question,
            meta={"mode": "answer_question"},
        )

        # If the error metabolism organ already produced a final answer, just return it.
        # Heuristic: if it contains "I don't know yet" we treat it as a learning request.
        if "I don't know yet" in em_resp:
            return em_resp

        # Otherwise, run the reasoning organ with the same question and EM context.
        reasoner_input = (
            f"Question: {question}\n\n"
            f"Initial thoughts (from Error Metabolism organ):\n{em_resp}\n\n"
            "Now reason step-by-step and give a final answer."
        )
        reasoned = self.think_with_organ(
            "reasoner",
            reasoner_input,
            meta={"mode": "answer_question_reasoned"},
        )
        return reasoned

    def learn_concept(self, concept_name: str, lesson_block: Dict[str, Any]) -> str:
        """
        Feed Janet a single lesson (one chunk from the curriculum)
        and log both her inner monologue + final restatement.
        """
        explanation = lesson_block.get("explanation", "")
        examples = lesson_block.get("examples", [])
        grade = lesson_block.get("grade", None)

        lesson_text = [
            f"Concept: {concept_name}",
            f"Grade level: {grade}",
            "",
            "Teacher explanation:",
            explanation,
            "",
            "Examples:",
        ]

        for ex in examples:
            q = ex.get("Q") or ex.get("q")
            a = ex.get("A") or ex.get("a")
            lesson_text.append(f"Q: {q}  |  A: {a}")

        full_lesson = "\n".join(lesson_text)

        # Use reasoner organ to process the lesson content as internalization.
        resp = self.think_with_organ(
            "reasoner",
            message=(
                "You are learning a new concept.\n\n"
                + full_lesson
                + "\n\nRestate the rule of this concept in simple terms.\n"
                  "Only output what you think and your final restatement.\n"
                  "If helpful, you may also include simple steps that explain how to apply it."
            ),
            meta={"mode": "learn_concept", "concept": concept_name, "grade": grade},
        )

        # Store both “inner thoughts” and “final answer” for now.
        concept_record = {
            "lesson": lesson_block,
            "janet_inner_monologue": resp,
            "janet_final_output": resp,
        }

        self.memory.store_concept(concept_name, concept_record)
        return resp


# ---------- Simple CLI Harness for Manual Testing ----------

def main():
    print("Janet v0.1 harness loaded.")
    print("NOTE: Using Chatty-20B via backend_chatty20b.py as Janet's backend.\n")

    janet = Janet()

    while True:
        try:
            text = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not text:
            continue

        if text.lower() in {"quit", "exit"}:
            print("Goodbye.")
            break

        if text.startswith("/learn "):
            concept = text[len("/learn "):].strip() or "demo_concept"
            demo_lesson = {
                "concept": concept,
                "grade": 0,
                "explanation": f"This is a demo explanation for {concept}.",
                "examples": [
                    {"Q": "Example question 1", "A": "Example answer 1"},
                    {"Q": "Example question 2", "A": "Example answer 2"},
                ],
            }
            print(f"[Teaching concept: {concept}]")
            resp = janet.learn_concept(concept, demo_lesson)
            print("Janet (restated rule):")
            print(resp)
            print()
            continue

        # Default: treat as a question.
        resp = janet.answer_question(text)
        print("Janet >")
        print(resp)
        print()


if __name__ == "__main__":
    main()
