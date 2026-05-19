import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, jsonify, request

from app.services.transaction_service import extract_transactions_from_file

extract_bp = Blueprint("extract", __name__, url_prefix="/ocr")


@extract_bp.post("/extract")
def extract():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    suffix = Path(uploaded_file.filename or "").suffix
    temp_file = NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    temp_file.close()

    try:
        uploaded_file.save(temp_path)
        result = extract_transactions_from_file(temp_path)
        return jsonify({"success": True, **result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
