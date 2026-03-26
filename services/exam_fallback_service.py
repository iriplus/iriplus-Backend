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
        """
        Build fallback items for:
        1. Cloze test with options
        """
        text = (
            f"[{level}] Emma had always wanted to improve her English, so when she "
            "saw an advertisement for a weekend course, she decided to sign up. "
            "At first, she was nervous because she did not know anyone there, but "
            "the teacher made everyone feel comfortable. By the end of the first day, "
            "she had already made some new friends and felt much more confident."
        )

        return [
            {
                "text": text,
                "gaps": [
                    {
                        "gap_number": 1,
                        "question": "Emma had always wanted to ___ her English.",
                        "options": ["improve", "increase", "rise", "developed"],
                        "answer": "improve",
                    },
                    {
                        "gap_number": 2,
                        "question": "She decided to ___ up for the course.",
                        "options": ["write", "sign", "join", "take"],
                        "answer": "sign",
                    },
                    {
                        "gap_number": 3,
                        "question": "At first, she was nervous because she did not ___ anyone there.",
                        "options": ["know", "meet", "recognize", "watch"],
                        "answer": "know",
                    },
                    {
                        "gap_number": 4,
                        "question": "The teacher made everyone feel ___.",
                        "options": ["easy", "relaxed", "comfortable", "quiet"],
                        "answer": "comfortable",
                    },
                    {
                        "gap_number": 5,
                        "question": "By the end of the day, she felt more ___.",
                        "options": ["careful", "confident", "certainly", "success"],
                        "answer": "confident",
                    },
                ],
            }
        ]

    @staticmethod
    def _build_open_cloze_test_items(level: str) -> list[dict[str, Any]]:
        """
        Build fallback items for:
        2. Open cloze test
        """
        text = (
            f"[{level}] Lucy had been looking forward to the school trip for weeks. "
            "When the day finally arrived, she got up early so as not to be late. "
            "She packed everything she needed and left home with plenty of time to spare. "
            "By the time she reached the station, most of her classmates had already arrived."
        )

        return [
            {
                "text": text,
                "gaps": [
                    {
                        "gap_number": 1,
                        "question": "Lucy had been looking forward ___ the school trip for weeks.",
                        "answer": "to",
                    },
                    {
                        "gap_number": 2,
                        "question": "When the day finally arrived, she got ___ early.",
                        "answer": "up",
                    },
                    {
                        "gap_number": 3,
                        "question": "She got up early so ___ not to be late.",
                        "answer": "as",
                    },
                    {
                        "gap_number": 4,
                        "question": "She left home with plenty of time to ___.",
                        "answer": "spare",
                    },
                    {
                        "gap_number": 5,
                        "question": "By the time she reached the station, most classmates had already ___.",
                        "answer": "arrived",
                    },
                ],
            }
        ]

    @staticmethod
    def _build_word_formation_items(level: str) -> list[dict[str, Any]]:
        """
        Build fallback items for:
        3. Word Formation
        """
        return [
            {
                "question": (
                    f"[{level}] The manager appreciated her ______ and promoted her quickly."
                ),
                "base_word": "HONEST",
                "answer": "honesty",
            },
            {
                "question": (
                    f"[{level}] It was a very ______ experience, and I learned a lot from it."
                ),
                "base_word": "VALUE",
                "answer": "valuable",
            },
            {
                "question": (
                    f"[{level}] The weather was so ______ that we decided to stay inside."
                ),
                "base_word": "PLEASE",
                "answer": "unpleasant",
            },
            {
                "question": (
                    f"[{level}] She completed the task quickly and ______."
                ),
                "base_word": "EFFICIENCY",
                "answer": "efficiently",
            },
            {
                "question": (
                    f"[{level}] There is still too much ______ about the final decision."
                ),
                "base_word": "CONFUSE",
                "answer": "confusion",
            },
        ]

    @staticmethod
    def _build_key_word_transformation_items(level: str) -> list[dict[str, Any]]:
        """
        Build fallback items for:
        4. Key word transformation
        """
        return [
            {
                "question": (
                    f"[{level}] Original sentence: I last saw Marta three months ago."
                ),
                "keyword": "SEEN",
                "prompt": "I ______ Marta for three months.",
                "answer": "have not seen",
            },
            {
                "question": (
                    f"[{level}] Original sentence: It was unnecessary for Tom to bring his laptop."
                ),
                "keyword": "HAVE",
                "prompt": "Tom ______ his laptop.",
                "answer": "did not have to bring",
            },
            {
                "question": (
                    f"[{level}] Original sentence: The film was too boring for us to finish."
                ),
                "keyword": "ENOUGH",
                "prompt": "The film was ______ for us to finish.",
                "answer": "not interesting enough",
            },
            {
                "question": (
                    f"[{level}] Original sentence: 'Why do not we go out for dinner?' Anna said."
                ),
                "keyword": "SUGGESTED",
                "prompt": "Anna ______ out for dinner.",
                "answer": "suggested going",
            },
            {
                "question": (
                    f"[{level}] Original sentence: Perhaps James forgot about the meeting."
                ),
                "keyword": "MIGHT",
                "prompt": "James ______ about the meeting.",
                "answer": "might have forgotten",
            },
        ]

    @staticmethod
    def _build_multiple_choice_items(level: str) -> list[dict[str, Any]]:
        """
        Build fallback items for:
        5. Multiple Choice
        """
        return [
            {
                "question": f"[{level}] If I had more free time, I ______ a new language.",
                "options": ["learn", "would learn", "will learn", "learned"],
                "answer": "would learn",
            },
            {
                "question": f"[{level}] She has worked here ______ 2021.",
                "options": ["for", "since", "during", "from"],
                "answer": "since",
            },
            {
                "question": f"[{level}] We were tired, ______ we continued working.",
                "options": ["because", "although", "but", "unless"],
                "answer": "but",
            },
            {
                "question": f"[{level}] The book ______ by the time I arrived.",
                "options": ["was sold", "had been sold", "has sold", "sold"],
                "answer": "had been sold",
            },
            {
                "question": f"[{level}] You ______ smoke here. It is forbidden.",
                "options": ["must not", "do not have to", "might not", "would not"],
                "answer": "must not",
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
                    f"[{level}] Complete this generic fallback item for exercise type: "
                    f"{exercise_name}. Item 1."
                ),
                "answer": "Sample answer 1",
            },
            {
                "question": (
                    f"[{level}] Complete this generic fallback item for exercise type: "
                    f"{exercise_name}. Item 2."
                ),
                "answer": "Sample answer 2",
            },
            {
                "question": (
                    f"[{level}] Complete this generic fallback item for exercise type: "
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