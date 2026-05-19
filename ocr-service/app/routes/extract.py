import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, jsonify, request

from app.services.transaction_service import extract_transactions_from_file

logger = logging.getLogger(__name__)

extract_bp = Blueprint("extract", __name__, url_prefix="/ocr")


@extract_bp.post("/extract")
def extract():
    """Extract transactions from uploaded bank statement."""
    logger.info(f"Received extraction request from {request.remote_addr}")
    
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        logger.warning("No file uploaded in extraction request")
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    # Validate file extension
    filename = uploaded_file.filename or "unknown"
    suffix = Path(filename).suffix.lower()
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    
    if suffix not in allowed_extensions:
        logger.warning(f"Unsupported file type: {suffix}")
        return jsonify({
            "success": False,
            "error": f"Unsupported file type: {suffix}. Allowed: {', '.join(allowed_extensions)}"
        }), 400
    
    # Save to temporary file
    temp_file = NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    temp_file.close()

    try:
        logger.info(f"Processing file: {filename} (size: {len(uploaded_file.read())} bytes)")
        uploaded_file.seek(0)  # Reset file pointer after reading size
        uploaded_file.save(temp_path)
        logger.info(f"Saved temporary file to: {temp_path}")
        
        # Extract transactions
        result = extract_transactions_from_file(temp_path)
        
        logger.info(f"Extraction successful: {result['summary']['transaction_count']} transactions")
        return jsonify({
            "success": True,
            **result
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Extraction failed: {str(e)}"
        }), 500
        
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")
