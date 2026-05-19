import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from app.routes.extract import extract_bp

load_dotenv()


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
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
