"""Analytics controller for the Home dashboard.

This module exposes role-aware analytics payloads for the authenticated user.
For now, only the Coordinator dashboard is implemented.

Rules applied consistently:
- Soft-deleted records are excluded.
- Users must be verified to be counted.
- Only the minimum required data is returned for each role.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func
from calendar import month_name
from datetime import date
from typing import Any
from orm_models import db, User, Class
from utils.types_enum import UserType

TUITION_STATUS_UP_TO_DATE = "up_to_date"
TUITION_STATUS_DELINQUENT = "delinquent"
TUITION_STATUS_NO_DATA = "no_data"

MONTH_NAME_TO_NUMBER: dict[str, int] = {
    name.lower(): index
    for index, name in enumerate(month_name)
    if index > 0
}

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


def home_analytics_controller():
    """Return the Home analytics payload for the authenticated user.

    Current behavior:
    - Coordinator: returns the real Coordinator dashboard payload.
    - Teacher/Student: returns 501 until their analytics are implemented.

    Returns:
        200 with the role-specific dashboard payload.
        403 if the authenticated user is not verified.
        404 if the authenticated user does not exist or was deleted.
        501 for roles not implemented yet.
    """
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

    return jsonify(
        {"message": "Dashboard analytics are not implemented for this role yet."}
    ), 501

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
