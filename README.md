# Bank Statement Extractor (DIFM)

A comprehensive system for extracting, parsing, and analyzing bank statements using OCR technology.

## Project Overview

This project consists of three main components:

### 1. **Frontend** (Next.js + TypeScript)
- Modern React-based UI for uploading bank statements
- Real-time progress tracking
- Transaction viewing and filtering
- Export functionality

### 2. **Backend** (Node.js + Express)
- RESTful API for document management
- User authentication & authorization
- Queue-based asynchronous processing
- Transaction database management
- File upload handling

### 3. **OCR Service** (Python + Flask)
- Automated bank statement parsing
- Table and row detection
- Text extraction and OCR processing
- Data validation and structuring

## Tech Stack

### Frontend
- Next.js 14+
- TypeScript
- Tailwind CSS
- Axios for HTTP client
- React Hooks

### Backend
- Node.js
- Express.js
- PostgreSQL
- Redis (caching & queues)
- Multer (file uploads)
- Bull (job queues)

### OCR Service
- Python 3.9+
- Flask
- PaddleOCR
- OpenCV
- PIL/Pillow

### Infrastructure
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

## Project Structure

```
bank-statement-extractor/
├── frontend/                 # Next.js application
├── backend/                  # Node.js API server
├── ocr-service/             # Python OCR microservice
├── shared/                  # Shared types and schemas
├── storage/                 # File storage (volumes)
├── database/                # Database schemas and migrations
├── docker-compose.yml       # Docker orchestration
└── README.md               # This file
```

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local OCR development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd bank-statement-extractor
   ```

2. **Create environment files**
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp ocr-service/.env.example ocr-service/.env
   cp frontend/.env.local.example frontend/.env.local
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database** (first time only)
   ```bash
   docker-compose exec postgres psql -U postgres -d bank_extractor -f /docker-entrypoint-initdb.d/schema.sql
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - OCR Service: http://localhost:8000

### Local Development

#### Backend Setup
```bash
cd backend
npm install
npm run dev
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### OCR Service Setup
```bash
cd ocr-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Upload
- `POST /api/upload` - Upload bank statement file
- `GET /api/upload/:id` - Get upload details
- `GET /api/uploads` - List all user uploads

### Transactions
- `GET /api/transactions` - List all transactions
- `GET /api/transactions/:id` - Get transaction details
- `POST /api/transactions/export` - Export transactions (CSV/Excel)

### OCR Service
- `POST /ocr/extract` - Extract data from document
- `GET /ocr/health` - Health check

## Environment Variables

### Backend (.env)
```
NODE_ENV=development
API_PORT=5000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bank_extractor
DB_USER=postgres
DB_PASSWORD=password
REDIS_HOST=localhost
REDIS_PORT=6379
OCR_SERVICE_URL=http://localhost:8000
JWT_SECRET=your-secret-key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### OCR Service (.env)
```
FLASK_ENV=development
OCR_PORT=8000
PADDLE_LANGUAGE=en
```

## Features

- ✅ Multi-format document support (PDF, PNG, JPG)
- ✅ Accurate OCR-based text extraction
- ✅ Automatic transaction parsing
- ✅ Real-time upload progress tracking
- ✅ Transaction history management
- ✅ Data export (CSV, Excel)
- ✅ User authentication
- ✅ Responsive UI design
- ✅ Error handling & logging
- ✅ Scalable microservice architecture

## Database Schema

### Main Tables
- **users** - User accounts
- **uploads** - File uploads
- **bank_statements** - Parsed bank statements
- **transactions** - Extracted transactions

See [database/schema.sql](database/schema.sql) for full schema.

## Performance Considerations

1. **File Processing**
   - Large files (>50MB) are chunked
   - Queue-based processing prevents blocking
   - Async job workers handle OCR tasks

2. **Caching**
   - Redis caching for frequently accessed data
   - Session management with Redis

3. **Database**
   - Indexed queries for transaction lookups
   - Pagination for large result sets

## Troubleshooting

### Services won't start
```bash
docker-compose down
docker-compose up -d --build
```

### Database connection issues
```bash
docker-compose logs postgres
docker-compose exec postgres pg_isready
```

### OCR service errors
```bash
docker-compose logs ocr-service
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please create an issue on GitHub or contact the development team.
