from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any
import pandas as pd
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from orm_models import User, db
from utils.types_enum import UserType, MonthName


REQUIRED_COLUMNS = {"dni", "last_paid_month", "payment_date"}
ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}


def _get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return f".{filename.rsplit('.', 1)[1].lower()}"


def _normalize_headers(columns: list[Any]) -> list[str]:
    return [str(column).strip().lower() for column in columns]


def _normalize_value(value: Any) -> str | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    return text


def _normalize_dni(value: Any) -> str | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    # Handles Excel numeric cells like 12345678.0
    if text.endswith(".0"):
        text = text[:-2]

    return text

def _parse_last_paid_month(value: Any) -> str | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    normalized = text.lower().capitalize()

    try:
        return MonthName(normalized).value
    except ValueError:
        return None

def _parse_payment_date(value: Any) -> date | None:
    if pd.isna(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None

    return parsed.date()


def _read_uploaded_file() -> pd.DataFrame:
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        raise ValueError("Missing file field. Expected multipart/form-data with a 'file' field.")

    if not uploaded_file.filename:
        raise ValueError("No file selected.")

    extension = _get_extension(uploaded_file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid file type. Allowed types: .csv, .xls, .xlsx.")

    file_bytes = uploaded_file.read()
    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    file_buffer = BytesIO(file_bytes)

    if extension == ".csv":
        dataframe = pd.read_csv(file_buffer)
    else:
        dataframe = pd.read_excel(file_buffer)

    if dataframe.empty:
        raise ValueError("The uploaded file has no rows.")

    dataframe.columns = _normalize_headers(list(dataframe.columns))
    return dataframe


def upload_tuitions_controller():
    """
    Validate and process a tuition upload file.

    Expected file columns:
        - dni
        - last_paid_month
        - payment_date

    Returns:
        JSON response with success message or validation errors.
    """
    try:
        dataframe = _read_uploaded_file()

        missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)
        if missing_columns:
            return jsonify({
                "message": (
                    "The file is missing required columns: "
                    f"{', '.join(sorted(missing_columns))}"
                )
            }), 400

        working_df = dataframe[list(REQUIRED_COLUMNS)].copy()

        working_df["dni"] = working_df["dni"].apply(_normalize_dni)
        working_df["last_paid_month"] = working_df["last_paid_month"].apply(_parse_last_paid_month)
        working_df["payment_date_parsed"] = working_df["payment_date"].apply(_parse_payment_date)

        validation_errors: list[str] = []

        for excel_row_number, (_, row) in enumerate(working_df.iterrows(), start=2):

            if row["dni"] is None:
                validation_errors.append(f"Row {excel_row_number}: dni is required.")

            if row["last_paid_month"] is None:
                validation_errors.append(
                    f"Row {excel_row_number}: last_paid_month is required and must be a valid month name in English."
                )

            if row["payment_date_parsed"] is None:
                validation_errors.append(f"Row {excel_row_number}: payment_date is invalid or empty.")

        duplicated_dnis = (
            working_df["dni"]
            .dropna()
            .value_counts()
        )
        duplicated_dnis = duplicated_dnis[duplicated_dnis > 1].index.tolist()

        if duplicated_dnis:
            validation_errors.append(
                "The file contains duplicated DNI values: "
                f"{', '.join(sorted(duplicated_dnis))}"
            )

        if validation_errors:
            return jsonify({
                "message": "File validation failed.",
                "errors": validation_errors,
            }), 400

        dni_list = working_df["dni"].dropna().tolist()

        students = (
            db.session.query(User)
            .filter(
                User.dni.in_(dni_list),
                User.type == UserType.STUDENT,
                User.date_deleted.is_(None),
                User.is_verified.is_(True),
            )
            .all()
        )

        students_by_dni = {student.dni: student for student in students}

        missing_or_invalid_dnis = sorted(
            [dni for dni in dni_list if dni not in students_by_dni]
        )

        if missing_or_invalid_dnis:
            return jsonify({
                "message": (
                    "Some DNI values do not exist, are not students, "
                    "are not verified, or were logically deleted."
                ),
                "invalid_dnis": missing_or_invalid_dnis,
            }), 400

        updated_students: list[str] = []

        for _, row in working_df.iterrows():
            student = students_by_dni[row["dni"]]

            # Replace these field names with your real model fields if needed.
            student.tuition_last_paid_month = row["last_paid_month"]
            student.tuition_payment_date = row["payment_date_parsed"]

            updated_students.append(student.dni)

        db.session.commit()

        return jsonify({
            "message": "Tuitions updated successfully.",
            "updated_count": len(updated_students),
            "updated_dnis": updated_students,
        }), 200

    except ValueError as err:
        return jsonify({"message": str(err)}), 400

    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500

    except Exception as err:  # pylint: disable=broad-except
        db.session.rollback()
        return jsonify({"message": f"Unexpected error: {err}"}), 500