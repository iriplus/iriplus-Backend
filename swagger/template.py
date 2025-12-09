swagger_template = {
    "openapi": "3.0.2",
    "info": {
        "title": "IRI+ API",
        "description": "Backend REST API documentation for the IRI+ platform.",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "/",
            "description": "Local server"
        }
    ],
    "tags": [
        {
            "name": "Auth",
            "description": "Authentication and session management"
        },
        {
            "name": "User",
            "description": "Operations related to user management"
        },
        {
            "name": "Level",
            "description": "Operations related to educational levels"
        },
        {
            "name": "Class",
            "description": "Operations related to classes"
        },
        {
            "name": "Exam",
            "description": "Create and manage exams"
        },
        {
            "name": "Exercise",
            "description": "Create and manage exercises"
        }
    ],
    "paths": {},
    "components": {
        "schemas": {
            "Level": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "description": {
                        "type": "string"
                    },
                    "cosmetic": {
                        "type": "string",
                        "nullable": True
                    },
                    "min_xp": {
                        "type": "integer"
                    },
                    "date_created": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True
                    }
                },
                "required": [
                    "description",
                    "min_xp"
                ]
            },
            "LevelInput": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string"
                    },
                    "cosmetic": {
                        "type": "string"
                    },
                    "min_xp": {
                        "type": "integer"
                    }
                },
                "required": [
                    "description", 
                    "min_xp"
                ]
            },
            "Class": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "example": 1
                    },
                    "class_code": {
                        "type": "string",
                        "example": "MATH101"
                    },
                    "description": {
                        "type": "string",
                        "example": "Basic Mathematics"
                    },
                    "suggested_level": {
                        "type": "string",
                        "example": "Beginner"
                    },
                    "max_capacity": {
                        "type": "integer",
                        "example": 30
                    },
                    "date_created": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True,
                        "example": "2025-01-10T14:32:05"
                    },
                    "date_deleted": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True,
                        "example": None
                    }
                },
                "required": [
                    "class_code",
                    "description",
                    "suggested_level",
                    "max_capacity"
                ]
            },
            "ClassInput": {
                "type": "object",
                "properties": {
                    "class_code": {
                        "type": "string",
                        "example": "MATH101"
                    },
                    "description": {
                        "type": "string",
                        "example": "Basic Mathematics"
                    },
                    "suggested_level": {
                        "type": "string",
                        "example": "Beginner"
                    },
                    "max_capacity": {
                        "type": "integer",
                        "example": 30
                    }
                },
                "required": [
                    "class_code",
                    "description",
                    "suggested_level",
                    "max_capacity"
                ]
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {
                    "type": "integer",
                    "example": 42
                    },
                    "name": {
                    "type": "string",
                    "example": "John"
                    },
                    "surname": {
                    "type": "string",
                    "example": "Doe"
                    },
                    "email": {
                    "type": "string",
                    "format": "email",
                    "example": "john@example.com"
                    },
                    "profile_picture": {
                    "type": "string",
                    "nullable": True,
                    "example": "https://example.com/avatar.png"
                    },
                    "type": {
                    "type": "string",
                    "enum": ["Student","Teacher","Coordinator"],
                    "example": "Student"
                    },
                    "dni": {
                    "type": "string",
                    "example": "40102938"
                    },
                    "accumulated_xp": {
                    "type": "integer",
                    "nullable": True,
                    "example": 1200
                    },
                    "date_created": {
                    "type": "string",
                    "format": "date-time",
                    "example": "2025-01-09T11:45:30"
                    },
                    "date_deleted": {
                    "type": "string",
                    "format": "date-time",
                    "nullable": True,
                    "example": None
                    }
                },
                "required": [
                    "id",
                    "name",
                    "surname",
                    "email",
                    "type",
                    "dni"
                ]
            },
            "UserInput": {
                "type": "object",
                "properties": {
                    "name": {
                    "type": "string",
                    "example": "John"
                    },
                    "surname": {
                    "type": "string",
                    "example": "Doe"
                    },
                    "email": {
                    "type": "string",
                    "format": "email",
                    "example": "john@example.com"
                    },
                    "passwd": {
                    "type": "string",
                    "example": "P@ssw0rd123"
                    },
                    "profile_picture": {
                    "type": "string",
                    "nullable": True,
                    "example": "https://example.com/avatar.png"
                    },
                    "dni": {
                    "type": "string",
                    "example": "40102938"
                    }
                },
                "required": [
                    "name",
                    "surname",
                    "email",
                    "passwd",
                    "dni"
                ]
            },
            "LoginInput": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "john@example.com"
                    },
                    "passwd": {
                        "type": "string",
                        "example": "P@ssw0rd123"
                    }
                },
                "required": ["email", "passwd"]
            },
            "AuthResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Login successful"
                    },
                    "user": {
                        "$ref": "#/components/schemas/User"
                    }
                }
            },
            "Exam": {
                "type": "object",
                "properties": {
                    "id": { "type": "integer" },
                    "status": { "type": "string", "example": "TEST_EXAM" },
                    "notes": { "type": "string", "nullable": True },
                    "class_id": { "type": "integer" },
                    "student_id": { "type": "integer", "nullable": True },
                    "coordinator_id": { "type": "integer", "nullable": True },
                    "date_created": { "type": "string", "format": "date-time" },
                    "date_deleted": { "type": "string", "format": "date-time", "nullable": True }
                },
                "required": [
                    "id",
                    "status",
                    "class_id"
                ]
            },
            "ExamInput": {
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "string",
                        "nullable": True,
                        "example": "Initial test exam"
                    },
                    "class_id": { "type": "integer" },
                    "student_id": {
                        "type": "integer",
                        "nullable": True
                    },
                    "coordinator_id": {
                        "type": "integer",
                        "nullable": True
                    }
                },
                "required": [
                    "class_id"
                ]
            },
            "Exercise": {
                "type": "object",
                "properties": {
                    "id": { "type": "integer" },
                    "archetype": { "type": "string", "example": "multiple-choice" },
                    "content": { "type": "string" },
                    "rubric": { "type": "string" },
                    "key": { "type": "string" },
                    "exam_id": { "type": "integer" },
                    "date_created": { "type": "string", "format": "date-time" },
                    "date_deleted": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True
                    }
                },
                "required": [
                    "id",
                    "archetype",
                    "content",
                    "rubric",
                    "key",
                    "exam_id"
                ]
            },
            "ExerciseInput": {
                "type": "object",
                "properties": {
                    "archetype": {
                        "type": "string",
                        "example": "multiple-choice"
                    },
                    "content": {
                        "type": "string",
                        "example": "What is 2 + 2?"
                    },
                    "rubric": {
                        "type": "string",
                        "example": "1 point for correct answer"
                    },
                    "key": {
                        "type": "string",
                        "example": "4"
                    },
                    "exam_id": {
                        "type": "integer",
                        "example": 1
                    }
                },
                "required": [
                    "archetype",
                    "content",
                    "rubric",
                    "key",
                    "exam_id"
                ]
            }
        },
        "responses": {
            "NotFound": {
                "description": "Resource not found"
            },
            "ValidationError": {
                "description": "Validation error"
            },
            "Unauthorized": {
                "description": "Unauthorized request"
            }
        }
    }
}
