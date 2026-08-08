"""Tests for per-exercise LLM generation and fallback isolation."""

import json
import unittest
from types import SimpleNamespace

from services.exam_generation_pipeline import (
    generate_exercise_blocks,
    parse_generated_exercise,
)


def _exercise(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        content_description=f"Description for {name}",
    )


def _block(name: str, question: str) -> dict:
    return {
        "exercise_type": name,
        "instructions": f"Complete the {name} exercise.",
        "items": [{"question": question, "answer": "answer"}],
    }


class TestExamGenerationPipeline(unittest.TestCase):
    """Validate one-call-per-type behavior and canonical block handling."""

    def test_generates_one_request_per_exercise_and_shares_previous_questions(self):
        exercises = [_exercise("Open Cloze"), _exercise("Word Formation")]
        prompts: list[str] = []
        previous_questions_seen: list[tuple[str, ...]] = []

        def prompt_builder(exercise, previous_questions, _index):
            previous_questions_seen.append(tuple(previous_questions))
            return exercise.name

        def llm_generator(prompt):
            prompts.append(prompt)
            return json.dumps({"exercise": _block(prompt, f"Question for {prompt}")})

        blocks = generate_exercise_blocks(
            exercise_types=exercises,
            prompt_builder=prompt_builder,
            llm_generator=llm_generator,
            fallback_builder=lambda exercise: _block(
                exercise.name,
                "Fallback question",
            ),
        )

        self.assertEqual(prompts, ["Open Cloze", "Word Formation"])
        self.assertEqual(previous_questions_seen[0], ())
        self.assertEqual(
            previous_questions_seen[1],
            ("Question for Open Cloze",),
        )
        self.assertEqual(
            [block["exercise_type"] for block in blocks],
            ["Open Cloze", "Word Formation"],
        )

    def test_invalid_response_falls_back_only_for_failed_exercise(self):
        exercises = [_exercise("Open Cloze"), _exercise("Word Formation")]
        fallback_calls: list[str] = []

        def llm_generator(prompt):
            if prompt == "Word Formation":
                return "not json"
            return json.dumps({"exercise": _block(prompt, "Generated question")})

        def fallback_builder(exercise):
            fallback_calls.append(exercise.name)
            return _block(exercise.name, "Fallback question")

        blocks = generate_exercise_blocks(
            exercise_types=exercises,
            prompt_builder=lambda exercise, _previous, _index: exercise.name,
            llm_generator=llm_generator,
            fallback_builder=fallback_builder,
        )

        self.assertEqual(fallback_calls, ["Word Formation"])
        self.assertEqual(blocks[0]["items"][0]["question"], "Generated question")
        self.assertEqual(blocks[1]["items"][0]["question"], "Fallback question")

    def test_rejects_an_unexpected_exercise_type(self):
        expected = _exercise("Open Cloze")
        raw_output = json.dumps(
            {"exercise": _block("Multiple Choice", "Generated question")}
        )

        with self.assertRaisesRegex(ValueError, "Expected exercise type"):
            parse_generated_exercise(raw_output, expected)

    def test_accepts_legacy_single_item_exercises_wrapper(self):
        expected = _exercise("Open Cloze")
        raw_output = json.dumps(
            {"exercises": [_block("open   cloze", " Generated question ")]}
        )

        block = parse_generated_exercise(raw_output, expected)

        self.assertEqual(block["exercise_type"], "Open Cloze")
        self.assertEqual(block["items"][0]["question"], "Generated question")


if __name__ == "__main__":
    unittest.main()
