1. Backend

cd backend
npm run dev
2. OCR service

cd ocr-service
.\.venv\Scripts\Activate.ps1
python -m app.main
3. Frontend

cd frontend
npm run dev
Then open:

http://localhost:3000
Expected ports:

Frontend: 3000
Backend: 5000
OCR: 8000