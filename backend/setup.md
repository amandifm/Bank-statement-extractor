# Setup Guide

This project consists of three services:

1. Backend API
2. Frontend
3. OCR Service

Create a `.env` file in each service directory and add the following configurations.

---

# Backend Environment Variables

Create:

```bash
backend/.env
```

Add:

```env
NODE_ENV=development
API_PORT=5000

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bank_extractor
DB_USER=postgres
DB_PASSWORD=2580

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# OCR Service Configuration
OCR_SERVICE_URL=http://localhost:8000

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRE=7d

# File Upload Configuration
MAX_FILE_SIZE=52428800
UPLOAD_DIRECTORY=./uploads
ALLOWED_FILE_TYPES=pdf,png,jpg,jpeg

# Queue Configuration
QUEUE_CONCURRENCY=3
QUEUE_MAX_ATTEMPTS=3

# Logging
LOG_LEVEL=debug
LOG_FORMAT=combined

# CORS
CORS_ORIGIN=http://localhost:3000

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# AWS S3 (Optional - Cloud Storage)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET=

# Application
APP_NAME=Bank Statement Extractor
APP_URL=http://localhost:5000
```

---

# Frontend Environment Variables

Create:

```bash
frontend/.env.local
```

Add:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000

# Application Settings
NEXT_PUBLIC_APP_NAME=Bank Statement Extractor
NEXT_PUBLIC_APP_ENV=development

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_EXPORT=true

# File Upload Settings
NEXT_PUBLIC_MAX_FILE_SIZE=52428800
NEXT_PUBLIC_ALLOWED_FILE_TYPES=.pdf,.png,.jpg,.jpeg

# Pagination
NEXT_PUBLIC_TRANSACTIONS_PER_PAGE=20

# UI Settings
NEXT_PUBLIC_THEME=light
```

---

# OCR Service Environment Variables

Create:

```bash
ocr-service/.env
```

Add:

```env
# Flask Configuration
FLASK_ENV=development
OCR_PORT=8000
DEBUG=True

# OCR Model Configuration
PADDLE_LANGUAGE=en
PADDLE_USE_GPU=False
PADDLE_DEVICE=cpu

# Processing Configuration
MAX_IMAGE_WIDTH=1920
MAX_IMAGE_HEIGHT=1920
IMAGE_QUALITY=85
MIN_CONFIDENCE_SCORE=0.5

# Processing Timeouts (in seconds)
OCR_TIMEOUT=60
PDF_CONVERSION_TIMEOUT=30

# Temporary File Configuration
TEMP_DIR=./app/temp
CLEANUP_TEMP_FILES=True
TEMP_FILE_MAX_AGE=86400

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# API Configuration
CORS_ORIGINS=http://localhost:5000,http://localhost:3000

# Model Cache
MODEL_CACHE_DIR=./models
AUTO_UPDATE_MODELS=True
```

---

# Service Ports

| Service | Port |
|----------|------|
| Frontend | 3000 |
| Backend API | 5000 |
| OCR Service | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

# Notes

- Ensure PostgreSQL and Redis are running before starting the backend.
- Update `JWT_SECRET` before deploying to production.
- Configure SMTP credentials only if email functionality is required.
- Configure AWS S3 credentials only if cloud storage is enabled.
- GPU OCR can be enabled by setting:

```env
PADDLE_USE_GPU=True
```
