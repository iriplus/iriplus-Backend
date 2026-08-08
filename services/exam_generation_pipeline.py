"""Reusable orchestration for generating one LLM response per exercise type."""

import json
from typing import Any, Callable, Sequence


PromptBuilder = Callable[[Any, Sequence[str], int], str]
LlmGenerator = Callable[[str], str]
FallbackBuilder = Callable[[Any], dict[str, Any]]


def extract_json_object(text: str) -> str:
    """Return the outermost JSON object contained in an LLM response."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model output")
    return text[start:end + 1]


def _normalized_name(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _extract_single_block(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept the new single-block schema and the old one-block list schema."""
    exercise = payload.get("exercise")
    if isinstance(exercise, dict):
        return exercise

    exercises = payload.get("exercises")
    if isinstance(exercises, list) and len(exercises) == 1:
        block = exercises[0]
        if isinstance(block, dict):
            return block

    if all(key in payload for key in ("exercise_type", "instructions", "items")):
        return payload

    raise ValueError("Model output must contain exactly one exercise block")


def validate_exercise_block(
    block: dict[str, Any],
    expected_exercise: Any,
) -> dict[str, Any]:
    """Validate and canonicalize one generated exercise block."""
    expected_name = str(expected_exercise.name).strip()
    returned_name = block.get("exercise_type")
    if not isinstance(returned_name, str):
        raise ValueError("Generated exercise is missing exercise_type")
    if _normalized_name(returned_name) != _normalized_name(expected_name):
        raise ValueError(
            f"Expected exercise type '{expected_name}', got '{returned_name}'"
        )

    instructions = block.get("instructions")
    if not isinstance(instructions, str):
        raise ValueError("Generated exercise is missing valid instructions")
    instructions = instructions.strip()
    if not instructions:
        instructions = (
            str(getattr(expected_exercise, "content_description", "")).strip()
            or expected_name
        )

    items = block.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Generated exercise must contain at least one item")

    canonical_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each generated item must be an object")

        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Each generated item must contain a valid question")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Each generated item must contain a valid answer")

        canonical_item = dict(item)
        canonical_item["question"] = question.strip()
        canonical_item["answer"] = answer.strip()
        canonical_items.append(canonical_item)

    return {
        "exercise_type": expected_name,
        "instructions": instructions,
        "items": canonical_items,
    }


def parse_generated_exercise(
    raw_output: str,
    expected_exercise: Any,
) -> dict[str, Any]:
    """Parse and validate a single-exercise LLM response."""
    payload = json.loads(extract_json_object(raw_output))
    if not isinstance(payload, dict):
        raise ValueError("Model output must be a JSON object")
    return validate_exercise_block(
        _extract_single_block(payload),
        expected_exercise,
    )


def generate_exercise_blocks(
    exercise_types: Sequence[Any],
    prompt_builder: PromptBuilder,
    llm_generator: LlmGenerator,
    fallback_builder: FallbackBuilder,
) -> list[dict[str, Any]]:
    """Generate exercises sequentially and isolate failures per exercise type."""
    blocks: list[dict[str, Any]] = []
    previous_questions: list[str] = []

    for index, exercise_type in enumerate(exercise_types):
        try:
            prompt = prompt_builder(exercise_type, tuple(previous_questions), index)
            raw_output = llm_generator(prompt)
            block = parse_generated_exercise(raw_output, exercise_type)
        except Exception as err:  # pylint: disable=broad-except
            print(
                f"Generation failed for exercise '{exercise_type.name}', "
                f"using its fallback: {err}"
            )
            fallback_block = fallback_builder(exercise_type)
            block = validate_exercise_block(fallback_block, exercise_type)

        blocks.append(block)
        previous_questions.extend(
            str(item["question"])
            for item in block["items"]
            if isinstance(item, dict) and item.get("question")
        )

    return blocks
