from orm_models import User, Level
def calculate_exam_xp(level: str, score: int, total_exercises: int) -> int:
    """
    Calculate XP earned for a corrected student exam.

    Formula:
        XP = score * total_exercises * level_multiplier

    Args:
        level: Class level description (e.g. A1, B2, FCE, CAE).
        score: Final exam score between 0 and 100.
        total_exercises: Total number of exercise blocks or items solved,
            depending on the business rule you decide to use.

    Returns:
        Integer XP amount, rounded to the nearest whole number.
    """

    if not isinstance(score, int):
        raise ValueError("score must be an integer")

    if not isinstance(total_exercises, int):
        raise ValueError("total_exercises must be an integer")

    if score < 0 or score > 100:
        raise ValueError("score must be between 0 and 100")

    if total_exercises < 0:
        raise ValueError("total_exercises must be greater than or equal to 0")

    normalized_level = (level or "").strip().upper()

    level_multipliers = {
        "A1": 10,
        "A2": 15,
        "B1": 20,
        "B2": 25,
        "C1": 30,
        "C2": 35,
        "FCE": 25,   # usually around B2
        "CAE": 30,   # usually around C1
        "CPE": 35,   # usually around C2
        "PET": 15,   # usually around A2
        "KET": 10,   # usually around A1
    }

    multiplier = level_multipliers.get(normalized_level, 1.00)

    xp = score * total_exercises * multiplier
    return int(round(xp))

def resolve_level_from_xp(accumulated_xp: int) -> Level | None:
    """
    Return the highest active level whose min_xp is less than or equal
    to the provided accumulated XP.
    """

    return (
        Level.query
        .filter(
            Level.date_deleted.is_(None),
            Level.min_xp <= accumulated_xp
        )
        .order_by(Level.min_xp.desc())
        .first()
    )


def apply_exam_xp_to_student(student: User, xp_gained: int) -> tuple[int, int | None, int | None]:
    """
    Add gained XP to the student and update their level if needed.

    Returns:
        A tuple with:
        - new_accumulated_xp
        - previous_level_id
        - new_level_id
    """

    previous_level_id = student.student_level_id
    current_xp = student.accumulated_xp or 0
    new_accumulated_xp = current_xp + xp_gained

    student.accumulated_xp = new_accumulated_xp

    new_level = resolve_level_from_xp(new_accumulated_xp)
    student.student_level_id = new_level.id if new_level else None

    return new_accumulated_xp, previous_level_id, student.student_level_id