from sqlalchemy import func
from orm_models import db, Exam, Class

NEUTRAL_BASELINE_SCORE = 57.5
EWMA_ALPHA = 0.65

CLASS_BASELINE_MIN_SAMPLES = 5
LEVEL_BASELINE_MIN_SAMPLES = 10
GLOBAL_BASELINE_MIN_SAMPLES = 20


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _ewma(scores: list[float], alpha: float = EWMA_ALPHA) -> float:
    """
    Exponential weighted moving average.
    Scores must be ordered from oldest to newest.
    """
    if not scores:
        return NEUTRAL_BASELINE_SCORE

    value = scores[0]
    for score in scores[1:]:
        value = (alpha * score) + ((1 - alpha) * value)
    return value


def _get_student_recent_scores(user_id: int, limit: int = 5) -> list[float]:
    """
    Returns recent scored exams for the student, ordered from oldest to newest.
    """
    rows = (
        db.session.query(Exam.score)
        .filter(Exam.user_id == user_id)
        .filter(Exam.score.isnot(None))
        .order_by(Exam.id.desc())
        .limit(limit)
        .all()
    )

    scores_desc = [float(row[0]) for row in rows]
    return list(reversed(scores_desc))


def _get_same_class_baseline(user_id: int, class_id: int) -> tuple[int, float | None]:
    count_value, avg_value = (
        db.session.query(func.count(Exam.id), func.avg(Exam.score))
        .filter(Exam.user_id != user_id)
        .filter(Exam.class_id == class_id)
        .filter(Exam.score.isnot(None))
        .one()
    )

    return int(count_value or 0), float(avg_value) if avg_value is not None else None


def _get_same_level_baseline(user_id: int, level: str) -> tuple[int, float | None]:
    count_value, avg_value = (
        db.session.query(func.count(Exam.id), func.avg(Exam.score))
        .join(Class, Class.id == Exam.class_id)
        .filter(Exam.user_id != user_id)
        .filter(Class.suggested_level == level)
        .filter(Exam.score.isnot(None))
        .one()
    )

    return int(count_value or 0), float(avg_value) if avg_value is not None else None


def _get_global_baseline(user_id: int) -> tuple[int, float | None]:
    count_value, avg_value = (
        db.session.query(func.count(Exam.id), func.avg(Exam.score))
        .filter(Exam.user_id != user_id)
        .filter(Exam.score.isnot(None))
        .one()
    )

    return int(count_value or 0), float(avg_value) if avg_value is not None else None


def _resolve_cohort_baseline(user_id: int, class_obj: Class) -> float:
    """
    Fallback hierarchy:
    same class -> same level -> global -> neutral constant
    """
    class_count, class_avg = _get_same_class_baseline(
        user_id=user_id,
        class_id=class_obj.id,
    )
    if class_count >= CLASS_BASELINE_MIN_SAMPLES and class_avg is not None:
        return _clamp_score(class_avg)

    level_count, level_avg = _get_same_level_baseline(
        user_id=user_id,
        level=class_obj.suggested_level,
    )
    if level_count >= LEVEL_BASELINE_MIN_SAMPLES and level_avg is not None:
        return _clamp_score(level_avg)

    global_count, global_avg = _get_global_baseline(user_id=user_id)
    if global_count >= GLOBAL_BASELINE_MIN_SAMPLES and global_avg is not None:
        return _clamp_score(global_avg)

    return NEUTRAL_BASELINE_SCORE


def _compute_trend_adjustment(scores: list[float]) -> float:
    """
    Small trend adjustment.
    Needs at least 3 exams to matter.
    Capped to avoid strong swings.
    """
    if len(scores) < 3:
        return 0.0

    recent_scores = scores[-2:]
    previous_scores = scores[:-2]

    recent_avg = _mean(recent_scores)
    previous_avg = _mean(previous_scores)

    delta = recent_avg - previous_avg

    # Only a small influence on the final prediction
    adjustment = delta * 0.25
    return max(-5.0, min(5.0, adjustment))


def predict_next_student_score(user_id: int, class_obj: Class) -> float:
    """
    Final online predictor.

    - If the student has no history, uses cohort baseline.
    - If the student has little history, blends student EWMA with cohort baseline.
    - If the student has enough history, gives more weight to student EWMA.
    """
    scores = _get_student_recent_scores(user_id=user_id, limit=5)
    cohort_baseline = _resolve_cohort_baseline(
        user_id=user_id,
        class_obj=class_obj,
    )

    if not scores:
        return round(cohort_baseline, 2)

    student_estimate = _ewma(scores)

    # Confidence by student history:
    # 1 exam  -> 0.2
    # 2 exams -> 0.4
    # 3 exams -> 0.6
    # 4+ exams -> 0.8
    student_weight = min(len(scores), 4) / 5.0

    trend_adjustment = _compute_trend_adjustment(scores)

    predicted_score = (
        (student_weight * student_estimate)
        + ((1.0 - student_weight) * cohort_baseline)
        + trend_adjustment
    )

    return round(_clamp_score(predicted_score), 2)


def get_difficulty_band(predicted_score: float) -> str:
    if predicted_score < 40:
        return "easier"
    if predicted_score > 75:
        return "harder"
    return "neutral"