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
                    "Many AI-enabled tools ___ behavior by suggesting next steps (push / nudge / force / remove)."
                ),
                "options": ["push", "nudge", "force", "remove"],
                "answer": "nudge",
            },
            {
                "question": (
                    "Employees are at risk of losing their ___, which is key to personal development (routine / agency / system / memory)."
                ),
                "options": ["routine", "agency", "system", "memory"],
                "answer": "agency",
            },
            {
                "question": (
                    "Executives worry that development paths are becoming too ___ (guided / random / chaotic / flexible)."
                ),
                "options": ["guided", "random", "chaotic", "flexible"],
                "answer": "guided",
            },
            {
                "question": (
                    "The main challenge is to ___ systems that preserve human choice (destroy / design / ignore / replace)."
                ),
                "options": ["destroy", "design", "ignore", "replace"],
                "answer": "design",
            },
            {
                "question": (
                    "We must decide whether to ___ agency to machines or retain human control (give / lose / cede / drop)."
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
                    "AI systems are changing the way people make ______ (ORGANIZE) decisions."
                ),
                "base_word": "ORGANIZE",
                "answer": "organizational",
            },
            {
                "question": (
                    "Many tools influence behavior through subtle ______ (SUGGEST)."
                ),
                "base_word": "SUGGEST",
                "answer": "suggestions",
            },
            {
                "question": (
                    "Losing agency can affect personal ______ (DEVELOP) and growth."
                ),
                "base_word": "DEVELOP",
                "answer": "development",
            },
            {
                "question": (
                    "Executives are concerned about the ______ (WEAK) of decision-making skills."
                ),
                "base_word": "WEAK",
                "answer": "weakening",
            },
            {
                "question": (
                    "It is important to design systems that allow ______ (DEPEND) thinking."
                ),
                "base_word": "DEPEND",
                "answer": "independent",
            },
        ]
    @staticmethod
    def _build_key_word_transformation_items(level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": "Original sentence: AI tools often suggest the next step to users. \nYour sentence: AI tools often ______ (PURPOSE) the next step to users.",
                "answer": "propose",
            },
            {
                "question": (
                    "Original sentence: Employees may lose their ability to make decisions. \nYour sentence: Employees ______ (RISK) their decision-making ability."
                ),
                "keyword": "RISK",
                "prompt": "Employees ______ their decision-making ability.",
                "answer": "risk losing",
            },
            {
                "question": (
                    "Original sentence: Executives are worried about reduced independence. \nYour sentence: Executives ______ (CONCERNED) reduced independence."
                ),
                "keyword": "CONCERNED",
                "prompt": "Executives ______ reduced independence.",
                "answer": "are concerned about",
            },
            {
                "question": (
                    "Original sentence: Systems should preserve space for reflection. \nYour sentence: Systems should ______ (ALLOW) reflection."
                ),
                "keyword": "ALLOW",
                "prompt": "Systems should ______ reflection.",
                "answer": "allow space for",
            },
            {
                "question": (
                    "Original sentence: We must decide whether machines take control. \nYour sentence: We must decide whether to ______ (CEDE) control to machines."
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
                "question": "AI tools can ___ (do / make / build / create) decisions automatically.",
                "options": ["do", "make", "build", "create"],
                "answer": "make",
            },
            {
                "question": "Employees need to ___ (take / do / make / bring) ownership of their decisions.",
                "options": ["take", "do", "make", "bring"],
                "answer": "take",
            },
            {
                "question": "The system often suggests ___ (a / the / an / one) next step.",
                "options": ["a", "the", "an", "one"],
                "answer": "the",
            },
            {
                "question": "Human agency is essential ___ (for / to / with / at) personal development.",
                "options": ["for", "to", "with", "at"],
                "answer": "for",
            },
            {
                "question": "People should think carefully ___ (about / on / with / to) what they want from AI.",
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

class StudentExamFallbackService:
    """
    Deterministic fallback generator for student exam creation.

    This fallback is used when the student generation flow fails during
    RAG retrieval, LLM generation, JSON parsing, or structural validation.
    """

    FALLBACK_CONTEXT = """An imagined town in Peru, an Eiffel tower in Beijing: travellers are increasingly using tools like ChatGPT for itinerary ideas – and being sent to destinations that don't exist.

Miguel Angel Gongora Meza, founder and director of Evolution Treks Peru, was in a rural Peruvian town preparing for a trek through the Andes when he overheard a curious conversation. Two unaccompanied tourists were chatting amicably about their plans to hike alone in the mountains to the "Sacred Canyon of Humantay".

"They [showed] me the screenshot, confidently written and full of vivid adjectives, [but] it was not true. There is no Sacred Canyon of Humantay!" said Gongora Meza. "The name is a combination of two places that have no relation to the description. The tourist paid nearly $160 (£118) in order to get to a rural road in the environs of Mollepata without a guide or [a destination]."

What's more, Gongora Meza insisted that this seemingly innocent mistake could have cost these travellers their lives. "This sort of misinformation is perilous in Peru," he explained. "The elevation, the climatic changes and accessibility [of the] paths have to be planned. When you [use] a program [like ChatGPT], which combines pictures and names to create a fantasy, then you can find yourself at an altitude of 4,000m without oxygen and [phone] signal."

In just a few years, artificial intelligence (AI) tools like ChatGPT, Microsoft Copilot and Google Gemini have gone from a mere novelty to an integral part of trip planning for millions of people. According to one survey, 30% of international travellers are now using generative AI tools and dedicated travel AI sites such as Wonderplan and Layla to help organise their trips."""

    @staticmethod
    def build_exam_payload(
        level: str,
        exercise_types: list[Any],
    ) -> dict[str, Any]:
        """
        Build a fallback payload with the same schema expected from the model.

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
            name = StudentExamFallbackService._normalize_name(exercise_type.name)

            if name == "cloze test with options":
                items = StudentExamFallbackService._build_cloze_test_with_options_items(level)
                instructions = (
                    "Read the text and choose the correct option (A, B, C or D) "
                    "for each gap."
                )
            elif name == "open cloze test":
                items = StudentExamFallbackService._build_open_cloze_test_items(level)
                instructions = (
                    "Read the text and complete each gap with one suitable word."
                )
            elif name == "word formation":
                items = StudentExamFallbackService._build_word_formation_items(level)
                instructions = (
                    "Use the word given in capitals to form a word that fits "
                    "correctly in each gap."
                )
            elif name == "key word transformation":
                items = StudentExamFallbackService._build_key_word_transformation_items(level)
                instructions = (
                    "Complete the second sentence so that it has a similar meaning "
                    "to the first sentence, using the key word given. Use between "
                    "3 and 6 words."
                )
            elif name == "multiple choice":
                items = StudentExamFallbackService._build_multiple_choice_items(level)
                instructions = (
                    "Choose the correct option (A, B, C or D) to complete each sentence."
                )
            else:
                items = StudentExamFallbackService._build_generic_items(
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
    def _build_cloze_test_with_options_items(_level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "Some travellers are sent to destinations that do not ___ (exist / arrive / travel / remain)."
                ),
                "options": ["exist", "arrive", "travel", "remain"],
                "answer": "exist",
            },
            {
                "question": (
                    "According to the guide, this kind of misinformation can be ___ (harmless / common / perilous / amusing)."
                ),
                "options": ["harmless", "common", "perilous", "amusing"],
                "answer": "perilous",
            },
        ]

    @staticmethod
    def _build_open_cloze_test_items(_level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": "The two tourists planned to hike alone ___ the mountains.",
                "answer": "in",
            },
            {
                "question": "According to one survey, 30% ___ international travellers use generative AI tools.",
                "answer": "of",
            },
        ]

    @staticmethod
    def _build_word_formation_items(_level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "The guide warned that false information could be extremely ______ (DANGER) for hikers."
                ),
                "base_word": "DANGER",
                "answer": "dangerous",
            },
            {
                "question": (
                    "Many people value the ______ (CONVENIENT) of AI tools when planning a trip."
                ),
                "base_word": "CONVENIENT",
                "answer": "convenience",
            },
        ]

    @staticmethod
    def _build_key_word_transformation_items(_level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": (
                    "Original sentence: The tourists believed the description because it looked very detailed. \nYour sentence: It was ______ (SUCH) detailed description that the tourists believed it."
                ),
                "keyword": "SUCH",
                "prompt": "It was ______ detailed description that the tourists believed it.",
                "answer": "such a",
            },
            {
                "question": (
                    "Original sentence: You must plan mountain routes carefully in Peru. \nYour sentence: Mountain travel in Peru ______ (NEEDS) planned carefully."
                ),
                "keyword": "NEEDS",
                "prompt": "Mountain travel in Peru ______ planned carefully.",
                "answer": "needs to be",
            },
        ]

    @staticmethod
    def _build_multiple_choice_items(_level: str) -> list[dict[str, Any]]:
        return [
            {
                "question": "Travellers often use AI tools to ___ (organize / avoid / cancel / reduce) their trips.",
                "options": ["organise", "avoid", "cancel", "reduce"],
                "answer": "organise",
            },
            {
                "question": "At high altitude, hikers may lose phone ___ (language / signal / memory / route).",
                "options": ["language", "signal", "memory", "route"],
                "answer": "signal",
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
        _ = level

        return [
            {
                "question": (
                    "Complete this fallback item for exercise type "
                    f"{exercise_name}. Item 1."
                ),
                "answer": "Sample answer 1",
            },
            {
                "question": (
                    "Complete this fallback item for exercise type "
                    f"{exercise_name}. Item 2."
                ),
                "answer": "Sample answer 2",
            },
        ]