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
from typing import cast, List
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from orm_models import db, Exam, Class, Exercise, ExamExerciseInstance
from services.rag_service import retrieve_course_context
from services.llm_service import build_prompt, generate_exam_from_llm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from flask import send_file
import io


def extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output")
    return text[start:end + 1]

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

    if not class_id or not context or not exercise_type_ids:
        return jsonify({"message": "Missing required fields"}), 400

    if not isinstance(exercise_type_ids, list) or not exercise_type_ids:
        return jsonify({"message": "exercise_type_ids must be a non-empty list"}), 400

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
            status="GENERATING",
            class_id=class_id,
            context=context,
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
            course_id=class_obj.class_code,
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
        new_exam.status = "Pending Review"

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
    

def get_full_exam(exam_id: int):
    """
    Return a fully reconstructed exam ready for frontend rendering.
    """

    try:
        exam = Exam.query.get(exam_id)
        if not exam or exam.date_deleted:
            return jsonify({"message": "Exam not found"}), 404

        """ if exam.status != "GENERATED":
            return jsonify({"message": "Exam not generated yet"}), 400 """

        result = {
            "id": exam.id,
            "status": exam.status,
            "class_id": exam.class_id,
            "context": exam.context,
            "exercises": []
        }

        for instance in exam.generated_exercises:
            exercise_type = Exercise.query.get(instance.exercise_type_id)

            result["exercises"].append({
                "exercise_type": exercise_type.name if exercise_type else None,
                "instructions": instance.instructions,
                "items": json.loads(instance.content_json)
            })

        return jsonify(result), 200

    except Exception as err:  # pylint: disable=broad-except
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

    html += f"<h1>Exam</h1>"
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
