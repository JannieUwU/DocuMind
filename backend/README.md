# Backend - FastAPI RAG Application

Python backend server providing RAG (Retrieval-Augmented Generation) capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Run the server
python -m uvicorn main:app --reload
```

The server will be available at http://localhost:8000

API Documentation: http://localhost:8000/docs

## 📦 Dependencies

Core dependencies in `requirements.txt`:

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **OpenAI** - AI API client
- **SQLAlchemy** - Database ORM
- **PyJWT** - JWT authentication
- **Pydantic** - Data validation
- **Python-multipart** - File upload support

## 🔧 Configuration

Create a `.env` file with:

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/database.db

# Security
SECRET_KEY=your_secret_key_here
MASTER_ENCRYPTION_KEY=your_encryption_key_here

# Application
ENVIRONMENT=development
DEBUG=true
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/          # Core functionality
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── main.py    # FastAPI application
│   ├── services/      # Business logic
│   │   └── custom_rag.py
│   └── utils/         # Utility functions
├── data/              # Database files
├── tests/             # Test files
├── main.py            # Entry point
└── requirements.txt   # Dependencies
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app/
```

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token

### Chat
- `POST /api/chat` - Send chat message
- `GET /api/chat/history` - Get chat history
- `DELETE /api/chat/{id}` - Delete conversation

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document

## 🔐 Security Features

- JWT-based authentication
- API key encryption
- Rate limiting (100 requests/minute)
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic

## 🗄️ Database

### SQLite (Development)
Default database stored in `data/users.db`

### PostgreSQL (Production)
Configure in `.env`:
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## 🚀 Deployment

### Production Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Docker

```bash
# Build image
docker build -t rag-backend -f deployment/docker/backend/Dockerfile .

# Run container
docker run -p 8000:8000 --env-file .env rag-backend
```

## 📊 Monitoring

Access the following endpoints:

- `/docs` - Swagger UI documentation
- `/redoc` - ReDoc documentation
- `/health` - Health check endpoint

## 🔍 Logging

Logs are stored in `logs/` directory:
- `app.log` - Application logs
- `error.log` - Error logs

Configure log level in `.env`:
```env
LOG_LEVEL=INFO
```

## 🛠️ Development

### Code Quality

```bash
# Run linter
pylint app/

# Format code
black app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

---

**Part of Vue3 RAG Hybrid Search Application**
