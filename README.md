# RAG Hybrid Search Application

A full-stack RAG (Retrieval-Augmented Generation) hybrid search application built with Vue 3 and FastAPI.

## Features

- **Intelligent Search**: Advanced RAG system with hybrid search capabilities
- **Real-time Chat**: Interactive conversation interface with AI-powered responses
- **Document Management**: Upload and manage documents for knowledge retrieval
- **User Authentication**: Secure JWT-based authentication system
- **Modern UI**: Responsive interface built with Vue 3 and Tailwind CSS
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation

## Project Structure

```
vue3-rag-frontend2/
├── frontend/              # Frontend application (Vue 3 + Vite)
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Frontend dependencies
│
├── backend/               # Backend application (FastAPI + Python)
│   ├── app/              # Application code
│   │   ├── core/         # Core modules
│   │   ├── services/     # Business services
│   │   ├── utils/        # Utility functions
│   │   └── main.py       # Application entry point
│   ├── data/             # Database files
│   ├── tests/            # Test directory
│   └── requirements.txt  # Python dependencies
│
├── docs/                  # Project documentation
├── deployment/            # Deployment configurations
├── tools/                 # Development tools
└── .github/               # GitHub configurations
```

## Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **OpenAI API Key** (for AI features)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:5173

### Backend Setup

```bash
cd backend

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

The backend will be available at: http://localhost:8000

API Documentation: http://localhost:8000/docs

## Technology Stack

### Frontend

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next-generation frontend build tool
- **Element Plus** - Vue 3 UI component library
- **Tailwind CSS** - Utility-first CSS framework
- **Pinia** - Vue state management
- **Axios** - HTTP client

### Backend

- **FastAPI** - Modern Python web framework
- **Python 3.11+** - Programming language
- **SQLite/PostgreSQL** - Database
- **OpenAI API** - AI integration
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **JWT** - Authentication

## Documentation

- [API Documentation](./docs/api/) - API endpoints and usage
- [Architecture Documentation](./docs/architecture/) - System design and architecture
- [Development Guide](./docs/development/) - Development setup and guidelines
- [Deployment Guide](./docs/deployment/) - Deployment instructions

## Configuration

### Frontend Configuration

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Backend Configuration

Edit `backend/.env`:

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

## Testing

### Frontend Tests

```bash
cd frontend
npm run test
```

### Backend Tests

```bash
cd backend
pytest tests/
```

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

See [Deployment Guide](./docs/deployment/) for detailed instructions.

## Security

- JWT-based authentication
- API key encryption
- Rate limiting
- CORS configuration
- Input validation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Contact

For questions and support, please open an issue on GitHub.

## Acknowledgments

- OpenAI for the AI API
- FastAPI community
- Vue.js community
- All contributors

---

**Built with ❤️ using Vue 3 and FastAPI**
