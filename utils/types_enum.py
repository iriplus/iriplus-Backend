"""Different types enumeration definition.

This module defines the different types enum, which is used to categorize 
different types of entities in the system
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

class ExamState(enum.Enum):
    """Enumeration for different exam states in the system."""

class ExerciseType(enum.Enum):
    """Enumeration for different exam states in the system."""
