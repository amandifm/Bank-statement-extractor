import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

# Keep Paddle/OpenCV CPU usage bounded on laptops. Users can override these in
# their environment if they run the OCR service on a larger machine.
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")

from app.routes.extract import extract_bp

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(extract_bp)

    @app.get("/health")
    @app.get("/ocr/health")
    def health():
        return jsonify(
            {
                "success": True,
                "status": "ok",
                "engine": "PaddleOCR",
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("OCR_PORT", "8000"))
    logger.info(f"Starting OCR service on port {port}")
    logger.info(f"Log level: {log_level}")
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
