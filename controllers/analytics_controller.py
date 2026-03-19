"""Analytics controller for the Home dashboard.

This module exposes role-aware analytics payloads for the authenticated user.
Implemented:
- Coordinator Dashboard
- Student Dashboard

Rules applied consistently:
- Soft-deleted records are excluded.
- Users must be verified to be counted.
- Only the minimum required data is returned for each role.
"""

from __future__ import annotations

from datetime import datetime, timedelta, date, time

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from calendar import month_name
from typing import Any
from orm_models import db, User, Class, Exam, Level
from utils.types_enum import UserType, ExamStatus

TUITION_STATUS_UP_TO_DATE = "up_to_date"
TUITION_STATUS_DELINQUENT = "delinquent"
TUITION_STATUS_NO_DATA = "no_data"

MONTH_NAME_TO_NUMBER: dict[str, int] = {
    name.lower(): index
    for index, name in enumerate(month_name)
    if index > 0
}
LEADERBOARD_LIMIT = 10
LAST_EXAMS_LIMIT = 5
WEEKLY_XP_DAYS = 7
DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _build_user_full_name(user: User) -> str:
    """Return the display name for a user.

    Args:
        user: User ORM instance.

    Returns:
        The user's full name with safe whitespace trimming.
    """
    return f"{user.name} {user.surname}".strip()


def _format_iso_date(value: datetime | None) -> str:
    """Format a datetime as an ISO date string.

    Args:
        value: Datetime to format.

    Returns:
        A YYYY-MM-DD string, or "-" when the value is missing.
    """
    if value is None:
        return "-"
    return value.date().isoformat()


def _count_enrolled_students(created_after: datetime | None = None) -> int:
    """Count active, verified students enrolled in active classes.

    Args:
        created_after: Optional lower bound for the student's creation date.

    Returns:
        The number of active and verified students currently enrolled in
        non-deleted classes.
    """
    query = (
        db.session.query(func.count(User.id))  # pylint: disable=not-callable
        .join(Class, Class.id == User.student_class_id)
        .filter(
            User.type == UserType.STUDENT,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
            User.student_class_id.isnot(None),
            Class.date_deleted.is_(None),
        )
    )

    if created_after is not None:
        query = query.filter(User.date_created >= created_after)

    return int(query.scalar() or 0)

# ---------------------------------------------------------------------------
# Coordinator helpers
# ---------------------------------------------------------------------------

def _calculate_average_course_occupancy() -> int:
    """Calculate the average occupancy percentage across active classes.

    Occupancy is calculated per class as:
        enrolled_active_verified_students / max_capacity * 100

    Returns:
        The rounded average occupancy percentage across all active classes.
        Returns 0 if no active classes exist.
    """
    active_classes = Class.query.filter(Class.date_deleted.is_(None)).all()

    if not active_classes:
        return 0

    student_counts_rows = (
        db.session.query(
            User.student_class_id,
            func.count(User.id),  # pylint: disable=not-callable
        )
        .join(Class, Class.id == User.student_class_id)
        .filter(
            User.type == UserType.STUDENT,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
            User.student_class_id.isnot(None),
            Class.date_deleted.is_(None),
        )
        .group_by(User.student_class_id)
        .all()
    )

    students_by_class_id: dict[int, int] = {
        int(class_id): int(count or 0)
        for class_id, count in student_counts_rows
        if class_id is not None
    }

    occupancy_percentages: list[float] = []

    for clazz in active_classes:
        if clazz.max_capacity <= 0:
            occupancy_percentages.append(0.0)
            continue

        enrolled_students = students_by_class_id.get(clazz.id, 0)
        occupancy = (enrolled_students / clazz.max_capacity) * 100
        occupancy_percentages.append(occupancy)

    return int(round(sum(occupancy_percentages) / len(occupancy_percentages)))


def _serialize_coordinator_dashboard() -> dict:
    """Build the Coordinator analytics payload for Home.

    Returns:
        A JSON-serializable dictionary containing only the metrics required
        by the Coordinator dashboard.
    """
    one_week_ago = datetime.now() - timedelta(days=7)

    return {
        "newEnrolledStudentsLastWeek": _count_enrolled_students(
            created_after=one_week_ago
        ),
        "totalEnrolledStudents": _count_enrolled_students(),
        "averageCourseOccupancy": _calculate_average_course_occupancy(),
    }


# ---------------------------------------------------------------------------
# Student helpers
# ---------------------------------------------------------------------------

def _build_empty_student_course_summary() -> dict:
    """Return a safe empty course summary for students without an active class.

    Returns:
        A default course summary payload.
    """
    return {
        "name": "No active course assigned",
        "description": (
            "You are not assigned to an active course yet. "
            "Please contact the institute staff if this looks incorrect."
        ),
        "teachers": ["Not assigned yet"],
        "studentsEnrolled": 0,
        "englishLevel": "Not assigned",
    }


def _get_active_levels() -> list[Level]:
    """Return all active levels ordered by minimum XP.

    Returns:
        A list of active Level ORM instances ordered ascending by min_xp.
    """
    return (
        Level.query
        .filter(Level.date_deleted.is_(None))
        .order_by(Level.min_xp.asc())
        .all()
    )


def _resolve_level_number(accumulated_xp: int, levels: list[Level]) -> int:
    """Resolve the numeric level position based on accumulated XP.

    Args:
        accumulated_xp: Current XP for the student.
        levels: Active levels ordered by min_xp ascending.

    Returns:
        The 1-based numeric level position.
    """
    if not levels:
        return 1

    current_level_number = 1

    for index, level in enumerate(levels, start=1):
        if accumulated_xp >= int(level.min_xp):
            current_level_number = index
        else:
            break

    return current_level_number


def _resolve_next_level_xp(accumulated_xp: int, levels: list[Level]) -> int:
    """Resolve the XP threshold for the next level.

    Args:
        accumulated_xp: Current XP for the student.
        levels: Active levels ordered by min_xp ascending.

    Returns:
        The min_xp of the next level, or the current XP when the student is
        already at the highest level.
    """
    for level in levels:
        if accumulated_xp < int(level.min_xp):
            return int(level.min_xp)

    return accumulated_xp

def _resolve_class_display_name(clazz: Class | None) -> str:
    """Return the preferred display name for a class."""
    if clazz is None or clazz.date_deleted is not None:
        return "-"

    if isinstance(clazz.description, str) and clazz.description.strip():
        return clazz.description.strip()

    if isinstance(clazz.class_code, str) and clazz.class_code.strip():
        return clazz.class_code.strip()

    return "-"


def _resolve_current_level(accumulated_xp: int, levels: list[Level]) -> Level | None:
    """Return the current Level ORM instance for the given XP."""
    current_level: Level | None = None

    for level in levels:
        if accumulated_xp >= int(level.min_xp):
            current_level = level
        else:
            break

    return current_level


def _resolve_next_level(accumulated_xp: int, levels: list[Level]) -> Level | None:
    """Return the next Level ORM instance for the given XP."""
    for level in levels:
        if accumulated_xp < int(level.min_xp):
            return level

    return None


def _resolve_level_name(accumulated_xp: int, levels: list[Level]) -> str:
    """Return the display name of the current level."""
    current_level = _resolve_current_level(accumulated_xp, levels)

    if current_level is None:
        return "Unranked"

    if isinstance(current_level.description, str) and current_level.description.strip():
        return current_level.description.strip()

    return f"Level {current_level.id}"


def _resolve_next_level_name(accumulated_xp: int, levels: list[Level]) -> str | None:
    """Return the display name of the next level."""
    next_level = _resolve_next_level(accumulated_xp, levels)

    if next_level is None:
        return None

    if isinstance(next_level.description, str) and next_level.description.strip():
        return next_level.description.strip()

    return f"Level {next_level.id}"


def _serialize_student_course_summary(student: User) -> dict:
    """Build the student's current course summary.

    Args:
        student: Authenticated student user.

    Returns:
        A JSON-serializable course summary payload.
    """
    clazz = student.student_class

    if clazz is None or clazz.date_deleted is not None:
        return _build_empty_student_course_summary()

    teacher_names = sorted(
        _build_user_full_name(teacher)
        for teacher in (clazz.teachers or [])
        if (
            teacher.date_deleted is None
            and teacher.is_verified is True
            and teacher.type == UserType.TEACHER
        )
    )

    if not teacher_names:
        teacher_names = ["Not assigned yet"]

    students_enrolled = int(
        db.session.query(func.count(User.id))  # pylint: disable=not-callable
        .filter(
            User.type == UserType.STUDENT,
            User.student_class_id == clazz.id,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
        )
        .scalar() or 0
    )

    return {
        "name": clazz.description,
        "description": (
            f"{clazz.description} course with a suggested English level of "
            f"{clazz.suggested_level}."
        ),
        "teachers": teacher_names,
        "studentsEnrolled": students_enrolled,
        "englishLevel": clazz.suggested_level,
    }


def _sort_students_for_leaderboard(
    students: list[User],
    levels: list[Level],
) -> list[User]:
    """Sort students by level first and XP second.

    Args:
        students: Student users to rank.
        levels: Active level definitions.

    Returns:
        The sorted student list in descending leaderboard order.
    """
    return sorted(
        students,
        key=lambda student: (
            -_resolve_level_number(int(student.accumulated_xp or 0), levels),
            -int(student.accumulated_xp or 0),
            _build_user_full_name(student).lower(),
        ),
    )


def _serialize_ranked_leaderboard(
    students: list[User],
    current_user_id: int,
    levels: list[Level],
    limit: int = LEADERBOARD_LIMIT,
) -> list[dict]:
    """Serialize a ranked leaderboard and always include the current student.

    Args:
        students: Student users to rank.
        current_user_id: Authenticated student's ID.
        levels: Active level definitions.
        limit: Maximum number of top entries to include before optionally
            appending the current student.

    Returns:
        A JSON-serializable leaderboard payload.
    """
    sorted_students = _sort_students_for_leaderboard(students, levels)

    leaderboard: list[dict] = []
    current_student_entry: dict | None = None

    for index, student in enumerate(sorted_students, start=1):
        accumulated_xp = int(student.accumulated_xp or 0)
        entry = {
            "rank": index,
            "name": _build_user_full_name(student),
            "level": _resolve_level_number(accumulated_xp, levels),
            "levelName": _resolve_level_name(accumulated_xp, levels),
            "xp": accumulated_xp,
            "isCurrentUser": student.id == current_user_id,
        }

        if index <= limit:
            leaderboard.append(entry)

        if student.id == current_user_id:
            current_student_entry = entry

    if current_student_entry is not None:
        already_included = any(
            entry.get("isCurrentUser") is True for entry in leaderboard
        )
        if not already_included:
            leaderboard.append(current_student_entry)

    return leaderboard


def _get_global_leaderboard_students() -> list[User]:
    """Return active, verified students enrolled in active classes.

    Returns:
        The list of student users eligible for the global leaderboard.
    """
    return (
        User.query
        .join(Class, Class.id == User.student_class_id)
        .filter(
            User.type == UserType.STUDENT,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
            User.student_class_id.isnot(None),
            Class.date_deleted.is_(None),
        )
        .all()
    )


def _get_course_leaderboard_students(class_id: int | None) -> list[User]:
    """Return active, verified students for the given class.

    Args:
        class_id: Class ID to filter by.

    Returns:
        The list of student users eligible for the course leaderboard.
    """
    if class_id is None:
        return []

    return (
        User.query
        .join(Class, Class.id == User.student_class_id)
        .filter(
            User.type == UserType.STUDENT,
            User.student_class_id == class_id,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
            Class.date_deleted.is_(None),
        )
        .all()
    )


def _serialize_student_weekly_xp(student_id: int) -> list[dict]:
    """Build the student's XP gain for the last 7 days.

    XP is counted using corrected exams with a non-null xp_gained value.

    Args:
        student_id: Student user ID.

    Returns:
        A list of seven points ordered from oldest to newest.
    """
    today = date.today()
    days = [
        today - timedelta(days=offset)
        for offset in reversed(range(WEEKLY_XP_DAYS))
    ]

    xp_by_day: dict[date, int] = {day: 0 for day in days}

    start_dt = datetime.combine(days[0], time.min)
    end_dt = datetime.combine(today + timedelta(days=1), time.min)

    exams = (
        Exam.query
        .filter(
            Exam.user_id == student_id,
            Exam.date_deleted.is_(None),
            Exam.corrected_at.isnot(None),
            Exam.xp_gained.isnot(None),
            Exam.corrected_at >= start_dt,
            Exam.corrected_at < end_dt,
        )
        .all()
    )

    for exam in exams:
        if exam.corrected_at is None:
            continue

        exam_day = exam.corrected_at.date()
        if exam_day in xp_by_day:
            xp_by_day[exam_day] += int(exam.xp_gained or 0)

    return [
        {
            "label": DAY_LABELS[day.weekday()],
            "value": xp_by_day[day],
        }
        for day in days
    ]


def _serialize_student_progress(student: User, levels: list[Level]) -> dict:
    """Build the student's current progress block.

    Args:
        student: Authenticated student user.
        levels: Active level definitions.

    Returns:
        A JSON-serializable progress payload.
    """
    current_xp = int(student.accumulated_xp or 0)

    return {
        "currentLevel": _resolve_level_number(current_xp, levels),
        "currentLevelName": _resolve_level_name(current_xp, levels),
        "currentXp": current_xp,
        "nextLevelXp": _resolve_next_level_xp(current_xp, levels),
        "nextLevelName": _resolve_next_level_name(current_xp, levels)
    }


def _serialize_student_last_exams(student_id: int) -> list[dict]:
    """Build the student's latest corrected exams list.

    Args:
        student_id: Student user ID.

    Returns:
        A JSON-serializable list of recent corrected exams.
    """
    order_expression = func.coalesce( # pylint: disable=assignment-from-no-return
        Exam.corrected_at,
        Exam.student_submitted_at,
        Exam.date_created,
    )

    exams = (
        Exam.query
        .filter(
            Exam.user_id == student_id,
            Exam.date_deleted.is_(None),
            Exam.corrected_at.isnot(None),
            Exam.score.isnot(None),
            Exam.xp_gained.isnot(None),
        )
        .order_by(order_expression.desc())
        .limit(LAST_EXAMS_LIMIT)
        .all()
    )

    payload: list[dict] = []

    for exam in exams:
        completed_at = (
            exam.student_submitted_at
            or exam.corrected_at
            or exam.date_created
        )

        payload.append(
            {
                "id": exam.id,
                "completedAt": _format_iso_date(completed_at),
                "context": exam.context or "No context available.",
                "grade": f"{int(exam.score or 0)} / 100",
                "xpAwarded": int(exam.xp_gained or 0),
            }
        )

    return payload


def _serialize_student_dashboard(student: User) -> dict:
    """Build the complete Student dashboard payload.

    Args:
        student: Authenticated student user.

    Returns:
        A JSON-serializable payload for the Student Home dashboard.
    """
    levels = _get_active_levels()

    return {
        "courseSummary": _serialize_student_course_summary(student),
        "leaderboards": {
            "course": _serialize_ranked_leaderboard(
                students=_get_course_leaderboard_students(student.student_class_id),
                current_user_id=student.id,
                levels=levels,
            ),
            "global": _serialize_ranked_leaderboard(
                students=_get_global_leaderboard_students(),
                current_user_id=student.id,
                levels=levels,
            ),
        },
        "weeklyXp": _serialize_student_weekly_xp(student.id),
        "progress": _serialize_student_progress(student, levels),
        "lastExams": _serialize_student_last_exams(student.id),
    }


# ---------------------------------------------------------------------------
# Teacher helpers
# ---------------------------------------------------------------------------

def _get_teacher_active_classes(teacher: User) -> list[Class]:
    """Return active classes assigned to the authenticated teacher."""
    if teacher.type != UserType.TEACHER:
        return []

    active_classes = [
        clazz
        for clazz in (teacher.teacher_classes or []) # type: ignore
        if clazz.date_deleted is None
    ]

    return sorted(
        active_classes,
        key=lambda clazz: (
            (clazz.description or "").lower(),
            (clazz.class_code or "").lower(),
            clazz.id,
        ),
    )


def _get_active_verified_students_for_class(class_id: int) -> list[User]:
    """Return active, verified students enrolled in an active class."""
    return (
        User.query
        .join(Class, Class.id == User.student_class_id)
        .filter(
            User.type == UserType.STUDENT,
            User.student_class_id == class_id,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
            Class.date_deleted.is_(None),
        )
        .all()
    )


def _get_teacher_names_for_class(clazz: Class) -> list[str]:
    """Return the display names of active verified teachers assigned to a class."""
    teacher_names = sorted(
        _build_user_full_name(teacher)
        for teacher in (clazz.teachers or []) # type: ignore
        if (
            teacher.date_deleted is None
            and teacher.is_verified is True
            and teacher.type == UserType.TEACHER
        )
    )

    return teacher_names or ["Not assigned yet"]


def _serialize_teacher_leaderboard(
    students: list[User],
    levels: list[Level],
) -> list[dict]:
    """Build the class leaderboard payload for the teacher dashboard."""
    sorted_students = _sort_students_for_leaderboard(students, levels)

    return [
        {
            "name": _build_user_full_name(student),
            "level": _resolve_level_number(int(student.accumulated_xp or 0), levels),
            "levelName": _resolve_level_name(int(student.accumulated_xp or 0), levels),
            "xp": int(student.accumulated_xp or 0),
        }
        for student in sorted_students
    ]


def _normalize_sql_date(raw_value) -> date | None:
    """Normalize DB date/group-by results into a Python date."""
    if raw_value is None:
        return None

    if isinstance(raw_value, date):
        return raw_value

    if isinstance(raw_value, datetime):
        return raw_value.date()

    try:
        return datetime.strptime(str(raw_value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _serialize_weekly_xp_by_student(
    students: list[User],
    levels: list[Level],
) -> list[dict]:
    """Build 7-day XP series for each student in the class.

    XP is counted from corrected exams with non-null xp_gained,
    exactly like the student dashboard.
    """
    if not students:
        return []

    today = date.today()
    days = [
        today - timedelta(days=offset)
        for offset in reversed(range(WEEKLY_XP_DAYS))
    ]

    student_ids = [student.id for student in students]
    xp_by_student_and_day: dict[int, dict[date, int]] = {
        student.id: {day: 0 for day in days}
        for student in students
    }

    start_dt = datetime.combine(days[0], time.min)
    end_dt = datetime.combine(today + timedelta(days=1), time.min)

    rows = (
        db.session.query(
            Exam.user_id,
            func.date(Exam.corrected_at),              # pylint: disable=not-callable
            func.sum(Exam.xp_gained),                 # pylint: disable=not-callable
        )
        .filter(
            Exam.user_id.in_(student_ids),
            Exam.date_deleted.is_(None),
            Exam.corrected_at.isnot(None),
            Exam.xp_gained.isnot(None),
            Exam.corrected_at >= start_dt,
            Exam.corrected_at < end_dt,
        )
        .group_by(Exam.user_id, func.date(Exam.corrected_at))
        .all()
    )

    for user_id, raw_day, total_xp in rows:
        normalized_day = _normalize_sql_date(raw_day)
        if normalized_day is None:
            continue
        if user_id in xp_by_student_and_day and normalized_day in xp_by_student_and_day[user_id]:
            xp_by_student_and_day[user_id][normalized_day] = int(total_xp or 0)

    sorted_students = _sort_students_for_leaderboard(students, levels)

    return [
        {
            "name": _build_user_full_name(student),
            "values": [
                {
                    "label": DAY_LABELS[day.weekday()],
                    "value": xp_by_student_and_day[student.id][day],
                }
                for day in days
            ],
        }
        for student in sorted_students
    ]


def _serialize_teacher_exam_queue(
    class_id: int,
    statuses: list[str],
) -> list[dict]:
    """Serialize teacher exam tables for a class and a set of statuses."""
    exams = (
        Exam.query
        .join(Class, Class.id == Exam.class_id)
        .filter(
            Exam.class_id == class_id,
            Exam.date_deleted.is_(None),
            Exam.status.in_(statuses),
            Class.date_deleted.is_(None),
        )
        .order_by(Exam.date_created.desc())
        .all()
    )

    payload: list[dict] = []

    for exam in exams:
        payload.append(
            {
                "id": exam.id,
                "generationDate": _format_iso_date(exam.date_created),
                "context": exam.context or "No context available.",
                "className": exam.class_exam.description if exam.class_exam else "-",
            }
        )

    return payload


def _serialize_pending_correction_exams(class_id: int) -> list[dict]:
    """Build exams pending teacher correction for a class."""
    return _serialize_teacher_exam_queue(
        class_id,
        [ExamStatus.PENDING_CORRECTION.value],
    )


def _serialize_pending_review_exams(class_id: int) -> list[dict]:
    """Build exams pending coordinator review for a class."""
    return _serialize_teacher_exam_queue(
        class_id,
        [ExamStatus.PENDING_REVIEW.value],
    )


def _serialize_teacher_course_dashboard(
    clazz: Class,
    levels: list[Level],
) -> dict:
    """Build the teacher dashboard payload for one class."""
    active_students = _get_active_verified_students_for_class(clazz.id)

    return {
        "id": clazz.id,
        "name": clazz.description,
        "description": (
            f"{clazz.description} course with a suggested English level of "
            f"{clazz.suggested_level}."
        ),
        "teachers": _get_teacher_names_for_class(clazz),
        "studentsEnrolled": len(active_students),
        "englishLevel": clazz.suggested_level,
        "leaderboard": _serialize_teacher_leaderboard(active_students, levels),
        "weeklyXpByStudent": _serialize_weekly_xp_by_student(
            active_students,
            levels,
        ),
        "pendingCorrectionExams": _serialize_pending_correction_exams(clazz.id),
        "pendingReviewExams": _serialize_pending_review_exams(clazz.id),
    }


def _serialize_teacher_dashboard(teacher_id: int) -> dict:
    """Build the complete Teacher dashboard payload."""
    teacher = db.session.get(User, teacher_id)

    if not teacher or teacher.date_deleted is not None:
        return {"courses": []}

    levels = _get_active_levels()
    teacher_classes = _get_teacher_active_classes(teacher)

    return {
        "courses": [
            _serialize_teacher_course_dashboard(clazz, levels)
            for clazz in teacher_classes
        ]
    }

# ---------------------------------------------------------------------------
# Public controller
# ---------------------------------------------------------------------------

def home_analytics_controller():
    """Return the Home analytics payload for the authenticated user.

    Current behavior:
    - Coordinator: returns the real Coordinator dashboard payload.
    - Student: returns the real Student dashboard payload
    - Teacher: returns 501 until their analytics are implemented.

    Returns:
        200 with the role-specific dashboard payload.
        403 if the authenticated user is not verified.
        404 if the authenticated user does not exist or was deleted.
        501 for roles not implemented yet.
        500 for unexpected server errors.
    """
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)

        if not user or user.date_deleted is not None:
            return jsonify({"message": "User not found."}), 404

        if user.is_verified is False:
            return jsonify({"message": "Email not verified."}), 403

        if user.type == UserType.COORDINATOR:
            return jsonify(
                {
                    "role": user.type.value,
                    "dashboard": {
                        "coordinator": _serialize_coordinator_dashboard(),
                    },
                }
            ), 200
        if user.type == UserType.STUDENT:
            return jsonify(
                {
                    "role": user.type.value,
                    "dashboard": {
                        "student": _serialize_student_dashboard(user)
                    },
                }
            ), 200
        if user.type == UserType.TEACHER:
            return jsonify(
                {
                    "role": user.type.value,
                    "dashboard": {
                        "teacher": _serialize_teacher_dashboard(user.id),
                    },
                }
            ), 200

        return jsonify(
            {
                "message": (
                    "Dashboard analytics are not implemented for this role yet."
                )
            }
        ), 501
    except SQLAlchemyError as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err: # pylint: disable-broad-except
        return jsonify({"message": f"Unexpected error: {err}"}), 500

def _get_active_verified_students() -> list[User]:
    """Return all active and verified students."""
    return (
        User.query.filter(
            User.type == UserType.STUDENT,
            User.date_deleted.is_(None),
            User.is_verified.is_(True),
        )
        .order_by(User.surname.asc(), User.name.asc())
        .all()
    )

def _normalize_paid_month(paid_month: str | None) -> int | None:
    """Convert an English month name into its numeric representation."""
    if paid_month is None:
        return None

    normalized_value = paid_month.strip().lower()
    if not normalized_value:
        return None

    return MONTH_NAME_TO_NUMBER.get(normalized_value)

def _build_paid_period(
    paid_month: str | None,
    payment_date: date | datetime | None,
) -> date | None:
    """Build the paid period using the stored month and payment date year."""
    month_number = _normalize_paid_month(paid_month)
    if month_number is None or payment_date is None:
        return None

    payment_year = (
        payment_date.year
        if isinstance(payment_date, (date, datetime))
        else None
    )
    if payment_year is None:
        return None

    return date(payment_year, month_number, 1)

def _calculate_months_overdue(
    paid_month: str | None,
    payment_date: date | datetime | None,
    today: date | None = None,
) -> int | None:
    """Calculate how many months overdue a student is."""
    reference_date = today or date.today()
    paid_period = _build_paid_period(paid_month, payment_date)

    if paid_period is None:
        return None

    current_period = date(reference_date.year, reference_date.month, 1)
    months_difference = (
        (current_period.year - paid_period.year) * 12
        + (current_period.month - paid_period.month)
    )

    return max(months_difference, 0)

def _resolve_tuition_status(
    paid_month: str | None,
    payment_date: date | datetime | None,
) -> tuple[str, int | None]:
    """Resolve the tuition status and overdue months for a student."""
    months_overdue = _calculate_months_overdue(paid_month, payment_date)

    if months_overdue is None:
        return TUITION_STATUS_NO_DATA, None

    if months_overdue == 0:
        return TUITION_STATUS_UP_TO_DATE, 0

    return TUITION_STATUS_DELINQUENT, months_overdue

def _serialize_tuition_payment_date(
    payment_date: date | datetime | None,
) -> str | None:
    """Serialize a tuition payment date into ISO format."""
    if payment_date is None:
        return None

    if isinstance(payment_date, datetime):
        return payment_date.date().isoformat()

    return payment_date.isoformat()

def _serialize_tuition_student(student: User) -> dict[str, Any]:
    """Serialize a student row for the tuition analytics payload."""
    paid_month = student.tuition_last_paid_month
    payment_date = student.tuition_payment_date
    status, months_overdue = _resolve_tuition_status(paid_month, payment_date)

    full_name = " ".join(
        part.strip()
        for part in [student.name or "", student.surname or ""]
        if part and part.strip()
    )

    return {
        "id": student.id,
        "name": student.name,
        "surname": student.surname,
        "fullName": full_name,
        "dni": student.dni,
        "status": status,
        "monthsOverdue": months_overdue,
        "lastPaidMonth": paid_month,
        "lastPaymentDate": _serialize_tuition_payment_date(payment_date),
    }

def _calculate_percentage(count: int, total: int) -> float:
    """Calculate a percentage rounded to two decimals."""
    if total == 0:
        return 0.0

    return round((count / total) * 100, 2)

def _serialize_tuition_dashboard() -> dict[str, Any]:
    """Build the Coordinator tuition analytics payload."""
    students = _get_active_verified_students()
    student_rows = [_serialize_tuition_student(student) for student in students]

    total_students = len(student_rows)

    up_to_date_count = sum(
        1
        for row in student_rows
        if row["status"] == TUITION_STATUS_UP_TO_DATE
    )
    delinquent_count = sum(
        1
        for row in student_rows
        if row["status"] == TUITION_STATUS_DELINQUENT
    )
    no_data_count = sum(
        1
        for row in student_rows
        if row["status"] == TUITION_STATUS_NO_DATA
    )

    students_with_three_or_more_months_overdue = [
        {
            "id": row["id"],
            "fullName": row["fullName"],
            "dni": row["dni"],
            "monthsOverdue": row["monthsOverdue"],
        }
        for row in student_rows
        if isinstance(row["monthsOverdue"], int) and row["monthsOverdue"] >= 3
    ]

    students_with_three_or_more_months_overdue.sort(
        key=lambda row: (-int(row["monthsOverdue"]), row["fullName"])
    )

    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "totalStudents": total_students,
            "counts": {
                "upToDate": up_to_date_count,
                "delinquent": delinquent_count,
                "noData": no_data_count,
            },
            "percentages": {
                "upToDate": _calculate_percentage(
                    up_to_date_count, total_students
                ),
                "delinquent": _calculate_percentage(
                    delinquent_count, total_students
                ),
                "noData": _calculate_percentage(
                    no_data_count, total_students
                ),
            },
        },
        "studentsWithThreeOrMoreMonthsOverdue": (
            students_with_three_or_more_months_overdue
        ),
        "students": student_rows,
    }

def tuition_analytics_controller():
    """Return the Tuition analytics payload for the authenticated user."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user or user.date_deleted is not None:
        return jsonify({"message": "User not found."}), 404

    if user.is_verified is False:
        return jsonify({"message": "Email not verified."}), 403

    if user.type != UserType.COORDINATOR:
        return jsonify(
            {"message": "Tuition analytics are only available for coordinators."}
        ), 403

    return jsonify(
        {
            "role": user.type.value,
            "dashboard": {
                "tuition": _serialize_tuition_dashboard(),
            },
        }
    ), 200
