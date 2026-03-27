import json
from typing import Any


class ExamFallbackService:
    """
    Deterministic fallback generator for exam creation.

    This service builds a valid exam payload with the same structure expected
    from the LLM, so the normal persistence flow can be reused when the model
    fails or returns invalid JSON.
    """

    @staticmethod
    def build_exam_payload(
        level: str,
        exercise_types: list[Any],
    ) -> dict[str, Any]:
        """
        Build a fallback payload with the same schema as the LLM output.

        Expected output schema:
        {
            "exercises": [
                {
                    "exercise_type": "string",
                    "instructions": "string",
                    "items": [...]
                }
            ]
        }
        """
        exercises_payload: list[dict[str, Any]] = []

        for exercise_type in exercise_types:
            name = ExamFallbackService._normalize_name(exercise_type.name)

            if name == "cloze test with options":
                items = ExamFallbackService._build_cloze_test_with_options_items(level)
                instructions = (
                    "Read the text and choose the correct option (A, B, C or D) "
                    "for each gap."
                )
            elif name == "open cloze test":
                items = ExamFallbackService._build_open_cloze_test_items(level)
                instructions = (
                    "Read the text and complete each gap with one suitable word."
                )
            elif name == "word formation":
                items = ExamFallbackService._build_word_formation_items(level)
                instructions = (
                    "Use the word given in capitals to form a word that fits "
                    "correctly in each gap."
                )
            elif name == "key word transformation":
                items = ExamFallbackService._build_key_word_transformation_items(level)
                instructions = (
                    "Complete the second sentence so that it has a similar meaning "
                    "to the first sentence, using the key word given. Use between "
                    "3 and 6 words."
                )
            elif name == "multiple choice":
                items = ExamFallbackService._build_multiple_choice_items(level)
                instructions = (
                    "Choose the correct option (A, B, C or D) to complete each sentence."
                )
            else:
                items = ExamFallbackService._build_generic_items(
                    level=level,
                    exercise_name=exercise_type.name,
                )
                instructions = (
                    exercise_type.content_description
                    or f"Complete the {exercise_type.name} exercise."
                )

            exercises_payload.append(
                {
                    "exercise_type": exercise_type.name,
                    "instructions": instructions,
                    "items": items,
                }
            )

        return {"exercises": exercises_payload}

    @staticmethod
    def build_snapshot(
        reason: str,
        payload: dict[str, Any],
    ) -> str:
        """
        Build a JSON snapshot for storage in generated_snapshot when fallback is used.
        """
        return json.dumps(
            {
                "source": "fallback",
                "reason": reason,
                "payload": payload,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize exercise names for matching.
        """
        return " ".join(name.lower().strip().split())

    @staticmethod
    def _build_cloze_test_with_options_items(level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "Many AI-enabled tools ___ behavior by suggesting next steps. "
                    "(A) push, (B) nudge, (C) force, (D) remove."
                ),
                "options": ["push", "nudge", "force", "remove"],
                "answer": "nudge",
            },
            {
                "question": (
                    "Employees are at risk of losing their ___, which is key to personal development. "
                    "(A) routine, (B) agency, (C) system, (D) memory."
                ),
                "options": ["routine", "agency", "system", "memory"],
                "answer": "agency",
            },
            {
                "question": (
                    "Executives worry that development paths are becoming too ___. "
                    "(A) guided, (B) random, (C) chaotic, (D) flexible."
                ),
                "options": ["guided", "random", "chaotic", "flexible"],
                "answer": "guided",
            },
            {
                "question": (
                    "The main challenge is to ___ systems that preserve human choice. "
                    "(A) destroy, (B) design, (C) ignore, (D) replace."
                ),
                "options": ["destroy", "design", "ignore", "replace"],
                "answer": "design",
            },
            {
                "question": (
                    "We must decide whether to ___ agency to machines or retain human control. "
                    "(A) give, (B) lose, (C) cede, (D) drop."
                ),
                "options": ["give", "lose", "cede", "drop"],
                "answer": "cede",
            },
        ]
    @staticmethod
    def _build_open_cloze_test_items(level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "AI is becoming deeply embedded ___ organizational workflows."
                ),
                "answer": "in",
            },
            {
                "question": (
                    "These tools can strip people ___ the ability to reflect."
                ),
                "answer": "of",
            },
            {
                "question": (
                    "Employees are ___ danger of losing their agency."
                ),
                "answer": "in",
            },
            {
                "question": (
                    "The system often suggests the next step ___ the user."
                ),
                "answer": "for",
            },
            {
                "question": (
                    "It is time to think hard ___ what we want from the future."
                ),
                "answer": "about",
            },
        ]

    @staticmethod
    def _build_word_formation_items(level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "AI systems are changing the way people make ______ decisions."
                ),
                "base_word": "ORGANIZE",
                "answer": "organizational",
            },
            {
                "question": (
                    "Many tools influence behavior through subtle ______."
                ),
                "base_word": "SUGGEST",
                "answer": "suggestions",
            },
            {
                "question": (
                    "Losing agency can affect personal ______ and growth."
                ),
                "base_word": "DEVELOP",
                "answer": "development",
            },
            {
                "question": (
                    "Executives are concerned about the ______ of decision-making skills."
                ),
                "base_word": "WEAK",
                "answer": "weakening",
            },
            {
                "question": (
                    "It is important to design systems that allow ______ thinking."
                ),
                "base_word": "DEPEND",
                "answer": "independent",
            },
        ]
    @staticmethod
    def _build_key_word_transformation_items(level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "Original sentence: AI tools often suggest the next step to users."
                ),
                "keyword": "PROPOSE",
                "prompt": "AI tools often ______ the next step to users.",
                "answer": "propose",
            },
            {
                "question": (
                    "Original sentence: Employees may lose their ability to make decisions."
                ),
                "keyword": "RISK",
                "prompt": "Employees ______ their decision-making ability.",
                "answer": "risk losing",
            },
            {
                "question": (
                    "Original sentence: Executives are worried about reduced independence."
                ),
                "keyword": "CONCERNED",
                "prompt": "Executives ______ reduced independence.",
                "answer": "are concerned about",
            },
            {
                "question": (
                    "Original sentence: Systems should preserve space for reflection."
                ),
                "keyword": "ALLOW",
                "prompt": "Systems should ______ reflection.",
                "answer": "allow space for",
            },
            {
                "question": (
                    "Original sentence: We must decide whether machines take control."
                ),
                "keyword": "CEDE",
                "prompt": "We must decide whether to ______ control to machines.",
                "answer": "cede",
            },
        ]

    @staticmethod
    def _build_multiple_choice_items(level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": "AI tools can ___ decisions automatically.",
                "options": ["do", "make", "build", "create"],
                "answer": "make",
            },
            {
                "question": "Employees need to ___ ownership of their decisions.",
                "options": ["take", "do", "make", "bring"],
                "answer": "take",
            },
            {
                "question": "The system often suggests ___ next step.",
                "options": ["a", "the", "an", "one"],
                "answer": "the",
            },
            {
                "question": "Human agency is essential ___ personal development.",
                "options": ["for", "to", "with", "at"],
                "answer": "for",
            },
            {
                "question": "People should think carefully ___ what they want from AI.",
                "options": ["about", "on", "with", "to"],
                "answer": "about",
            },
        ]

    @staticmethod
    def _build_generic_items(
        level: str,
        exercise_name: str,
    ) -> list[dict[str, Any]]:
        """
        Generic fallback for any future exercise type not yet explicitly supported.
        """
        return [
            {
                "question": (
                    "Complete this generic fallback item for exercise type: "
                    f"{exercise_name}. Item 1."
                ),
                "answer": "Sample answer 1",
            },
            {
                "question": (
                    "Complete this generic fallback item for exercise type: "
                    f"{exercise_name}. Item 2."
                ),
                "answer": "Sample answer 2",
            },
            {
                "question": (
                    "Complete this generic fallback item for exercise type: "
                    f"{exercise_name}. Item 3."
                ),
                "answer": "Sample answer 3",
            },
        ]
    
    @staticmethod
    def extract_answers(items: list[dict[str, Any]]) -> list[Any]:
        """
        Extract answers from different fallback item structures.
        """
        answers: list[Any] = []

        for item in items:
            if "answer" in item:
                answers.append(item["answer"])
                continue

            if "gaps" in item and isinstance(item["gaps"], list):
                for gap in item["gaps"]:
                    answers.append(gap.get("answer"))

        return answers