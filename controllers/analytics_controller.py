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

from orm_models import db, User, Class
from utils.types_enum import UserType


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
