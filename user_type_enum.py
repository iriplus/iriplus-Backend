"""User type enumeration definition.

This module defines the UserType enum, which is used to categorize 
users in the system by their role.
"""

import enum


class UserType(enum.Enum):
    """Enumeration for different user roles in the system."""

    # Coordinator role: typically manages the system or courses
    COORDINATOR = "Coordinator"

    # Teacher role: represents instructors assigned to classes
    TEACHER = "Teacher"

    # Student role: represents learners enrolled in courses
    STUDENT = "Student"
