"""
Controller for AI-based exam generation.

This module orchestrates:

1. Input validation.
2. Class and exercise type validation.
3. Exam creation in GENERATING state.
4. RAG retrieval from Qdrant.
5. LLM prompt construction and generation.
6. JSON validation of LLM output.
7. Persistence of generated snapshot.
"""

import json
import datetime
from typing import cast, List
import io
from flask import request, jsonify, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from orm_models import db, Exam, Class, Exercise, ExamExerciseInstance, User
from services.rag_service import retrieve_course_context
from services.llm_service import build_prompt, generate_exam_from_llm, build_refinement_prompt
from utils.types_enum import ExamStatus


def extract_json(text: str) -> str:
    """
    Docstring for extract_json
    
    :param text: Description
    :type text: str
    :return: Description
    :rtype: str
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output")
    return text[start:end + 1]

#No asigna id de profesora al examen. No contempla la maquina de estados que hicimos
@jwt_required()
def generate_exam():
    """
    Generate a new exam using RAG + LLM.

    Expected JSON payload:
    {
        "class_id": int,
        "context": str,
        "exercise_type_ids": [int]
    }

    Returns:
        201 with exam_id if successful.
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    class_id = data.get("class_id")
    context = data.get("context")
    exercise_type_ids = data.get("exercise_type_ids")
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not class_id or not context or not exercise_type_ids:
        return jsonify({"message": "Missing required fields"}), 400

    if not isinstance(exercise_type_ids, list) or not exercise_type_ids:
        return jsonify({"message": "exercise_type_ids must be a non-empty list"}), 400
    if not user:
        return jsonify({"message":"Teacher not found"}), 404

    try:
        # ------------------------
        # Validate Class
        # ------------------------
        class_obj = Class.query.get(class_id)
        if not class_obj or class_obj.date_deleted:
            return jsonify({"message": "Class not found or deleted"}), 404

        # ------------------------
        # Validate Exercise Types
        # ------------------------
        exercise_types: List[Exercise] = []

        for ex_id in exercise_type_ids:
            ex = Exercise.query.get(ex_id)
            if not ex or ex.date_deleted:
                return jsonify(
                    {"message": f"Invalid exercise type id {ex_id}"}
                ), 400
            exercise_types.append(ex)

        # ------------------------
        # Create Exam (GENERATING)
        # ------------------------
        new_exam = Exam(
            status=ExamStatus.GENERATING.value,
            class_id=class_id,
            context=context,
            user_id=user_id
        )

        for ex in exercise_types:
            new_exam.exercise_types.append(ex)

        db.session.add(new_exam)
        db.session.flush()  # ensures new_exam.id exists

        # ------------------------
        # RAG Phase
        # ------------------------
        level = class_obj.suggested_level

        exercise_list_text = "\n".join(
            [f"- {ex.name}: {ex.content_description}" for ex in exercise_types]
        )

        contexts = retrieve_course_context(
            course_id=class_obj.description,
            level=level,
            exercises_description=exercise_list_text,
        )

        retrieved_context_text = "\n\n---\n\n".join(contexts)

        # ------------------------
        # LLM Phase
        # ------------------------
        prompt = build_prompt(
            level=level,
            teacher_text=context,
            exercise_list_text=exercise_list_text,
            retrieved_context=retrieved_context_text,
        )

        raw_output = generate_exam_from_llm(prompt)

        #print("----- MODEL RAW OUTPUT -----")
        #print(raw_output)
        #print("----- END MODEL OUTPUT -----")

        # ------------------------
        # Validate JSON
        # ------------------------
        try:
            cleaned_json = extract_json(raw_output)
            parsed_output = json.loads(cleaned_json)
            for exercise_block in parsed_output["exercises"]:
                exercise_name = exercise_block["exercise_type"]

                # buscar el exercise type en BD
                exercise_type = Exercise.query.filter(
                    db.func.lower(Exercise.name) == exercise_name.lower()
                ).first()

                if not exercise_type:
                    db.session.rollback()
                    return jsonify({
                        "message": f"Exercise type '{exercise_name}' not found in catalog"
                    }), 400

                instance = ExamExerciseInstance(
                    exam_id=new_exam.id,
                    exercise_type_id=exercise_type.id,
                    instructions=exercise_block["instructions"],
                    content_json=json.dumps(exercise_block["items"]),
                    answer_key_json=json.dumps({
                        "answers": [
                            item["answer"] for item in exercise_block["items"]
                        ]
                    })
                )
                db.session.add(instance)
        except Exception:
            db.session.rollback()
            return jsonify({"message": "Model did not return valid JSON"}), 500
        # Optional: minimal structural validation
        if "exercises" not in parsed_output:
            db.session.rollback()
            return jsonify({"message": "Invalid exam structure returned by model"}), 500

        # ------------------------
        # Persist Results
        # ------------------------
        new_exam.generated_snapshot = raw_output
        new_exam.status = ExamStatus.GENERATING.value

        db.session.commit()

        return jsonify(
            {
                "message": "Exam generated successfully",
                "exam_id": new_exam.id,
            }
        ), 201
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500

    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500

def refine_exam(exam_id: int):
    """
    Docstring for refine_exam
    
    :param exam_id: Description
    :type exam_id: int
    """
    data = request.get_json(silent=True)
    print("Data", data)
    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    feedback = data.get("feedback")
    if not feedback:
        return jsonify({"message": "Missing feedback"}), 400

    exam = Exam.query.get(exam_id)
    if not exam or exam.date_deleted:
        return jsonify({"message": "Exam not found"}), 404

    print(exam.status)
    print(exam.user_id)
    print(get_jwt_identity())
    if int(exam.user_id) != int(get_jwt_identity()):
        return jsonify({"message": "Unauthorized"}), 403

    if exam.status != ExamStatus.GENERATING.value:
        return jsonify({"message": "Exam is not editable in current state"}), 400

    try:
        # Nivel para el prompt (mismo criterio que en generate)
        level = exam.class_exam.suggested_level

        print("Level", level)
        refinement_prompt = build_refinement_prompt(
            level=level,
            original_snapshot=exam.generated_snapshot,
            teacher_feedback=feedback,
        )
        print("refinement promp", refinement_prompt)
        raw_output = generate_exam_from_llm(refinement_prompt)

        print("Raw Output", raw_output)
        cleaned_json = extract_json(raw_output)
        print("Cleaned Json", cleaned_json)
        parsed_output = json.loads(cleaned_json)
        print("Parsed Output", parsed_output)

        if "exercises" not in parsed_output:
            return jsonify({"message": "Invalid exam structure returned by model"}), 500

        # Validar que no cambien los exercise types originales
        original_types = {ex.name.lower() for ex in exam.exercise_types}
        returned_types = {
            ex_block["exercise_type"].lower()
            for ex_block in parsed_output["exercises"]
        }

        if original_types != returned_types:
            return jsonify({
                "message": "Refinement cannot change exercise types"
            }), 400

        # borrar instancias previas
        ExamExerciseInstance.query.filter_by(exam_id=exam.id).delete()

        for exercise_block in parsed_output["exercises"]:
            exercise_type = Exercise.query.filter(
                db.func.lower(Exercise.name)
                == exercise_block["exercise_type"].lower()
            ).first()

            # FIX Pylance: validar None explícitamente
            if not exercise_type:
                db.session.rollback()
                return jsonify({
                    "message": f"Exercise type '{exercise_block['exercise_type']}' not found"
                }), 400

            instance = ExamExerciseInstance(
                exam_id=exam.id,
                exercise_type_id=exercise_type.id,
                instructions=exercise_block["instructions"],
                content_json=json.dumps(exercise_block["items"]),
                answer_key_json=json.dumps({
                    "answers": [
                        item["answer"] for item in exercise_block["items"]
                    ]
                })
            )
            db.session.add(instance)

        exam.generated_snapshot = raw_output
        # estado se mantiene en GENERATING hasta "Send to review"
        exam.status = ExamStatus.GENERATING.value

        db.session.commit()

        return jsonify({"message": "Exam refined successfully"}), 200

    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": str(err)}), 500

def get_full_exam(exam_id: int):
    """
    Return a fully reconstructed exam ready for frontend rendering.
    """

    try:
        exam = (
            Exam.query
            .options(
                joinedload(Exam.class_exam), # type: ignore
                joinedload(Exam.user_exam),          # teacher # type: ignore
                joinedload(Exam.coordinator_exam),  # coordinator # type: ignore
                joinedload(Exam.generated_exercises) # type: ignore
            )
            .filter(
                Exam.id == exam_id,
                Exam.date_deleted.is_(None)
            )
            .first()
        )

        if not exam:
            return jsonify({"message": "Exam not found"}), 404

        result = {
            "id": exam.id,
            "status": exam.status,
            "context": exam.context,
            "notes": exam.notes,
            "date_created": exam.date_created,

            # Clase
            "class_id": exam.class_id,
            "class_description": (
                exam.class_exam.description
                if exam.class_exam else None
            ),

            # Profesora
            "teacher_id": exam.user_id,
            "teacher_full_name": (
                f"{exam.user_exam.name} {exam.user_exam.surname}"
                if exam.user_exam else None
            ),

            # Coordinadora
            "coordinator_id":exam.coordinator_id,
            "coordinator_full_name": (
                f"{exam.coordinator_exam.name} {exam.coordinator_exam.surname}"
                if exam.coordinator_exam else None
            ),

            "exercises": []
        }

        for instance in exam.generated_exercises:
            exercise_type = instance.exercise_type

            result["exercises"].append({
                "exercise_type": exercise_type.name if exercise_type else None,
                "instructions": instance.instructions,
                "items": json.loads(instance.content_json)
            })

        return jsonify(result), 200

    except Exception as err:
        return jsonify({"message": f"Unexpected error: {err}"}), 500

def build_exam_html(exam: Exam) -> str:
    """
    Build HTML representation of exam for PDF export.
    """

    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            h1 { text-align: center; }
            h2 { margin-top: 30px; }
            .question { margin-bottom: 10px; }
            .options { margin-left: 20px; }
            .page-break { page-break-before: always; }
        </style>
    </head>
    <body>
    """

    html += "<h1>Exam</h1>"
    html += f"<p><strong>Class ID:</strong> {exam.class_id}</p>"
    html += f"<p><strong>Date:</strong> {exam.date_created}</p>"
    html += "<hr>"

    generated_exercises = cast(List[ExamExerciseInstance], exam.generated_exercises)
    for instance in generated_exercises:
        items = json.loads(instance.content_json)

        html += f"<h2>{instance.exercise_type.name}</h2>"
        html += f"<p><em>{instance.instructions}</em></p>"

        for idx, item in enumerate(items, start=1):
            html += f"<div class='question'><strong>{idx}.</strong> {item['question']}</div>"

            if "options" in item:
                for option in item["options"]:
                    html += f"<div class='options'>{option}</div>"

        html += "<br>"

    # Answer sheet page
    html += "<div class='page-break'></div>"
    html += "<h1>Answer Sheet</h1>"

    generated_exercises = cast(List[ExamExerciseInstance], exam.generated_exercises)
    for instance in generated_exercises:
        answers = json.loads(instance.answer_key_json)["answers"]
        html += f"<h3>{instance.exercise_type.name}</h3>"
        for idx, ans in enumerate(answers, start=1):
            html += f"<p>{idx}. {ans}</p>"

    html += "</body></html>"

    return html


def export_exam_pdf(exam_id: int):
    """
    Generate a PDF version of a generated exam using ReportLab.
    """

    exam = Exam.query.get(exam_id)
    if not exam or exam.date_deleted:
        return jsonify({"message": "Exam not found"}), 404

    if exam.status != "GENERATED":
        return jsonify({"message": "Exam not generated yet"}), 400

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    normal_style = styles["Normal"]

    elements.append(Paragraph("Exam", title_style))
    elements.append(Spacer(1, 0.3 * inch))

    for instance in exam.generated_exercises:
        elements.append(Paragraph(instance.exercise_type.name, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(instance.instructions, normal_style))
        elements.append(Spacer(1, 0.2 * inch))

        items = json.loads(instance.content_json)

        for idx, item in enumerate(items, start=1):
            question_text = f"{idx}. {item['question']}"
            elements.append(Paragraph(question_text, normal_style))
            elements.append(Spacer(1, 0.1 * inch))

            if "options" in item:
                for option in item["options"]:
                    elements.append(Paragraph(option, normal_style))
                    elements.append(Spacer(1, 0.1 * inch))

        elements.append(Spacer(1, 0.3 * inch))

    # Answer sheet
    elements.append(PageBreak())
    elements.append(Paragraph("Answer Sheet", title_style))
    elements.append(Spacer(1, 0.3 * inch))

    for instance in exam.generated_exercises:
        elements.append(Paragraph(instance.exercise_type.name, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        answers = json.loads(instance.answer_key_json)["answers"]

        for idx, answer in enumerate(answers, start=1):
            elements.append(Paragraph(f"{idx}. {answer}", normal_style))
            elements.append(Spacer(1, 0.1 * inch))

        elements.append(Spacer(1, 0.3 * inch))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"exam_{exam_id}.pdf",
        mimetype="application/pdf"
    )

def export_exam_docx(exam_id: int):
    """
    Generate a DOCX version of a generated exam.
    """

    exam = Exam.query.get(exam_id)
    if not exam or exam.date_deleted:
        return jsonify({"message": "Exam not found"}), 404

    if exam.status != "GENERATED":
        return jsonify({"message": "Exam not generated yet"}), 400

    document = Document()

    # Title
    document.add_heading("Exam", level=1)

    document.add_paragraph(f"Class ID: {exam.class_id}")
    document.add_paragraph(f"Date: {exam.date_created}")
    document.add_paragraph("\n")

    # Exercises
    for instance in exam.generated_exercises:
        document.add_heading(instance.exercise_type.name, level=2)
        document.add_paragraph(instance.instructions)

        items = json.loads(instance.content_json)

        for idx, item in enumerate(items, start=1):
            document.add_paragraph(f"{idx}. {item['question']}")

            if "options" in item:
                for option in item["options"]:
                    document.add_paragraph(option, style="List Bullet")

        document.add_paragraph("\n")

    # Answer Sheet
    document.add_page_break()
    document.add_heading("Answer Sheet", level=1)

    for instance in exam.generated_exercises:
        document.add_heading(instance.exercise_type.name, level=2)

        answers = json.loads(instance.answer_key_json)["answers"]

        for idx, answer in enumerate(answers, start=1):
            document.add_paragraph(f"{idx}. {answer}")

        document.add_paragraph("\n")

    file_stream = io.BytesIO()
    document.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f"exam_{exam_id}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

def delete_exam(exam_id: int):
    """
    Docstring for delete_exam
    
    :param exam_id: Description
    :type exam_id: int
    """
    exam = Exam.query.get(exam_id)
    if not exam or exam.date_deleted:
        return jsonify({"message": "Exam not found"}), 404
    try:
        exam.date_deleted = datetime.datetime.now()
        db.session.commit()
        return jsonify({"message":f"Level {exam.id} deleted successfully"}), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": {f"Something went wrong: {err}"}}), 500

def get_all_exams_controller():
    """
    Docstring for get_all_exams_controller
    """
    try:
        current_user_id = get_jwt_identity()

        exams = (
            Exam.query
            .options(
                joinedload(Exam.class_exam),   # type: ignore
                joinedload(Exam.user_exam)     # type: ignore
            )
            .filter(
                Exam.date_deleted.is_(None),
                Exam.status != "Accepted",
                Exam.status != "Generating",
                or_(
                    Exam.coordinator_id.is_(None),
                    Exam.coordinator_id == current_user_id
                )
            )
            .all()
        )

        result = []
        for exam in exams:
            result.append({
                "id": exam.id,
                "status": exam.status,
                "context": exam.context,
                "class_id": exam.class_id,
                "class_description": exam.class_exam.description if exam.class_exam else None,
                "user_id": exam.user_id,
                "teacher_full_name": (
                    f"{exam.user_exam.name} {exam.user_exam.surname}"
                    if exam.user_exam else None
                ),
                "generated_exercises": [],
                "date_created": exam.date_created,
                "coordinator_id":exam.coordinator_id
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jwt_required()
def get_teacher_exams_controller():
    """
    Docstring for get_teacher_exams_controller
    """
    try:
        current_user_id = int(get_jwt_identity())
        exams = (
            Exam.query
            .options(
                joinedload(Exam.class_exam),         # type: ignore
                joinedload(Exam.coordinator_exam)    # type: ignore
            )
            .filter(
                Exam.date_deleted.is_(None),
                Exam.user_id == current_user_id,
                Exam.status != "Generating"
            )
            .all()
        )

        result = []
        for exam in exams:
            result.append({
                "id": exam.id,
                "status": exam.status,
                "context": exam.context,
                "class_id": exam.class_id,
                "class_description": (
                    exam.class_exam.description if exam.class_exam else None
                ),
                "user_id": exam.user_id,
                "date_created": exam.date_created,
                "coordinator_id": exam.coordinator_id,
                "coordinator_full_name": (
                    f"{exam.coordinator_exam.name} {exam.coordinator_exam.surname}"
                    if exam.coordinator_exam else None
                )
            })
        return jsonify(result), 200

    except Exception as err:  # pylint: disable=broad-except
        print(err)
        return jsonify({"error": str(err)}), 500

@jwt_required()
def get_student_exams_controller():
    """
    Docstring for get_student_exams_controller
    """
    try:
        current_user_id = int(get_jwt_identity())
        exams = (
            Exam.query
            .options(
                joinedload(Exam.class_exam),         # type: ignore
                joinedload(Exam.coordinator_exam)    # type: ignore
            )
            .filter(
                Exam.date_deleted.is_(None),
                Exam.user_id == current_user_id,
                Exam.status != "Generating"
            )
            .all()
        )

        result = []
        for exam in exams:
            result.append({
                "id": exam.id,
                "status": exam.status,
                "context": exam.context,
                "class_id": exam.class_id,
                "class_description": (
                    exam.class_exam.description if exam.class_exam else None
                ),
                "user_id": exam.user_id,
                "date_created": exam.date_created,
                "coordinator_id": exam.coordinator_id,
                "coordinator_full_name": (
                    f"{exam.coordinator_exam.name} {exam.coordinator_exam.surname}"
                    if exam.coordinator_exam else None
                )
            })
        return jsonify(result), 200

    except Exception as err:  # pylint: disable=broad-except
        print(err)
        return jsonify({"error": str(err)}), 500

def send_exam_to_review(exam_id: int):
    """
    Docstring for send_exam_to_review
    """
    try:
        current_user_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)
        if not exam or exam.date_deleted is not None:
            return jsonify({"error": "Exam not found"}), 404

        # Si lo tiene otra coordinadora → conflicto
        if exam.coordinator_id is not None and exam.coordinator_id != current_user_id:
            return jsonify({"error": "Exam already assigned to another coordinator"}), 409

        # Si no tiene coordinadora, asignar; si ya soy yo, mantener
        if exam.coordinator_id is None:
            exam.coordinator_id = current_user_id

        # Pasar a On Review siempre (reanudar)
        exam.status = "On Review"
        db.session.commit()

        return jsonify({"message": "Moved to On Review"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def leave_exam_review(exam_id: int):
    """
    Docstring for leave_exam_review
    """
    try:
        exam = Exam.query.get(exam_id)

        if not exam or exam.date_deleted is not None:
            return jsonify({"error": "Exam not found"}), 404

        # Solo permitir si está en revisión
        if exam.status != "On Review":
            return jsonify({"error": "Exam is not currently On Review"}), 400

        # Cambiar únicamente el estado
        exam.status = "Pending Review"
        db.session.commit()

        return jsonify({"message": "Exam moved back to Pending Review"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def accept_exam(exam_id: int):
    """
    Docstring for accept_exam
    """
    try:
        current_user_id = int(get_jwt_identity())  # ← clave

        exam = Exam.query.get(exam_id)
        if not exam or exam.date_deleted is not None:
            return jsonify({"error": "Exam not found"}), 404

        print("ACCEPT DEBUG coordinator_id:", exam.coordinator_id, type(exam.coordinator_id))
        print("ACCEPT DEBUG current_user_id:", current_user_id, type(current_user_id))

        # Solo la coordinadora asignada puede aceptar
        if exam.coordinator_id != current_user_id:
            return jsonify({"error": "Not authorized"}), 403

        exam.status = "Accepted"
        db.session.commit()

        return jsonify({"message": "Exam accepted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def send_to_correction(exam_id: int):
    """
    Docstring for send_to_correction
    """
    exam = Exam.query.get(exam_id)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404

    data = request.get_json()
    exam.status = "Pending Correction"
    exam.notes = data.get("notes")

    db.session.commit()
    return jsonify({"message": "Exam sent to correction"}), 200

@jwt_required()
def submit_correction(exam_id: int):
    """
    Persist manual teacher corrections and move the exam back to Pending Review.

    Expected payload:
    {
        "context": "updated context",
        "exercises": [
            {
                "exercise_type": "Word Formation",
                "items": [
                    {
                        "question": "Updated question",
                        "answer": "Updated answer"
                    }
                ]
            }
        ]
    }
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"message": "Invalid JSON body"}), 400
        print("Data", data)

        edited_context = data.get("context")
        edited_exercises = data.get("exercises")

        if not isinstance(edited_context, str) or not edited_context.strip():
            return jsonify({"message": "Context is required"}), 400

        if not isinstance(edited_exercises, list) or not edited_exercises:
            return jsonify({"message": "Exercises must be a non-empty list"}), 400

        exam = (
            Exam.query
            .filter(
                Exam.id == exam_id,
                Exam.date_deleted.is_(None)
            )
            .first()
        )

        if not exam:
            return jsonify({"message": "Exam not found"}), 404
        print("Exam data", exam, exam.user_id, exam.status)

        if int(exam.user_id) != current_user_id:
            return jsonify({"message": "Unauthorized"}), 403

        if exam.status != ExamStatus.PENDING_CORRECTION.value:
            return jsonify({
                "message": "Exam is not editable in current state"
            }), 400

        current_instances = cast(List[ExamExerciseInstance], exam.generated_exercises)

        print("Current", current_instances)
        if not current_instances:
            return jsonify({"message": "Exam has no generated exercises"}), 400

        if len(edited_exercises) != len(current_instances):
            return jsonify({
                "message": "You cannot change the number of exercise blocks"
            }), 400
        instances_by_type = {}
        for instance in current_instances:
            if not instance.exercise_type or not instance.exercise_type.name:
                return jsonify({"message": "Exam contains invalid exercise metadata"}), 500

            exercise_key = instance.exercise_type.name.strip().lower()

            if exercise_key in instances_by_type:
                return jsonify({
                    "message": "Duplicated exercise types are not supported"
                }), 400

            instances_by_type[exercise_key] = instance

        received_types = set()

        for exercise_block in edited_exercises:
            exercise_type_name = exercise_block.get("exercise_type")
            edited_items = exercise_block.get("items")

            if not isinstance(exercise_type_name, str) or not exercise_type_name.strip():
                return jsonify({"message": "Each exercise must include exercise_type"}), 400

            if not isinstance(edited_items, list):
                return jsonify({"message": "Each exercise must include an items list"}), 400

            exercise_key = exercise_type_name.strip().lower()

            if exercise_key in received_types:
                return jsonify({"message": "Duplicated exercise types in payload"}), 400

            instance = instances_by_type.get(exercise_key)
            if not instance:
                return jsonify({
                    "message": "You cannot change the exercise types of the exam"
                }), 400

            original_items = json.loads(instance.content_json)

            if len(edited_items) != len(original_items):
                return jsonify({
                    "message": (
                        f"You cannot change the number of items for "
                        f"'{exercise_type_name}'"
                    )
                }), 400

            updated_items = []
            updated_answers = []

            for index, (edited_item, original_item) in enumerate(
                zip(edited_items, original_items),
                start=1
            ):
                question = edited_item.get("question")
                answer = edited_item.get("answer")

                if not isinstance(question, str) or not question.strip():
                    return jsonify({
                        "message": (
                            f"Question {index} in '{exercise_type_name}' is required"
                        )
                    }), 400

                if not isinstance(answer, str) or not answer.strip():
                    return jsonify({
                        "message": (
                            f"Answer {index} in '{exercise_type_name}' is required"
                        )
                    }), 400

                updated_item = dict(original_item)
                updated_item["question"] = question.strip()
                updated_item["answer"] = answer.strip()

                updated_items.append(updated_item)
                updated_answers.append(answer.strip())

            instance.content_json = json.dumps(updated_items)
            instance.answer_key_json = json.dumps({
                "answers": updated_answers
            })

            received_types.add(exercise_key)

        exam.context = edited_context.strip()
        exam.status = ExamStatus.PENDING_REVIEW.value

        db.session.commit()

        return jsonify({
            "message": "Exam corrected and sent back to review"
        }), 200

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500

    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500
