# Development Guide

**Project:** Vue3 RAG Hybrid Search Application
**Version:** 1.0.0
**Last Updated:** 2025-12-05

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Git Workflow](#git-workflow)
6. [Testing Guidelines](#testing-guidelines)
7. [Debugging](#debugging)
8. [Common Issues](#common-issues)
9. [Best Practices](#best-practices)
10. [Contributing](#contributing)

---

## Getting Started

### Prerequisites

Ensure you have the following installed:

- **Node.js** 18.x or higher
- **npm** 9.x or higher
- **Python** 3.11 or higher
- **pip** latest version
- **Git** 2.x or higher
- **Visual Studio Code** (recommended) or your preferred IDE

### IDE Setup

#### Visual Studio Code Extensions

**Frontend Development:**
```
- Vue Language Features (Volar)
- TypeScript Vue Plugin (Volar)
- ESLint
- Prettier - Code formatter
- Tailwind CSS IntelliSense
- Auto Rename Tag
- Path Intellisense
```

**Backend Development:**
```
- Python
- Pylance
- Python Debugger
- autoDocstring
- Better Comments
- SQLite Viewer
```

**General:**
```
- GitLens
- Thunder Client (API testing)
- Error Lens
- Bracket Pair Colorizer
```

#### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "[vue]": {
    "editor.defaultFormatter": "Vue.volar"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

---

## Development Environment Setup

### Initial Setup

#### 1. Clone Repository

```bash
git clone <repository-url>
cd vue3-rag-frontend2
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env and configure
# VITE_API_BASE_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

#### 3. Backend Setup

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

# Create environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_key_here
# SECRET_KEY=generate_secure_key
# MASTER_ENCRYPTION_KEY=generate_secure_key

# Run database migrations (if applicable)
# alembic upgrade head

# Start development server
python -m uvicorn main:app --reload
```

Backend will be available at: http://localhost:8000

API Documentation: http://localhost:8000/docs

### Environment Variables

#### Frontend `.env`

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_DEBUG=true

# Optional
VITE_SENTRY_DSN=
```

#### Backend `.env`

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/database.db
# For PostgreSQL:
# DATABASE_TYPE=postgresql
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# Security
SECRET_KEY=your-secret-key-min-32-chars
MASTER_ENCRYPTION_KEY=your-encryption-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
UPLOAD_LIMIT_PER_HOUR=10
CHAT_LIMIT_PER_MINUTE=30

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=pdf,txt,md
```

---

## Project Structure

### Frontend Structure

```
frontend/
├── public/                # Static assets (not processed by Vite)
│   ├── favicon.ico
│   └── logo.png
│
├── src/
│   ├── assets/           # Processed assets (images, fonts)
│   │   ├── images/
│   │   └── styles/
│   │       └── main.css
│   │
│   ├── components/       # Reusable Vue components
│   │   ├── chat/
│   │   │   ├── ChatMessage.vue
│   │   │   ├── ChatInput.vue
│   │   │   └── MessageList.vue
│   │   ├── document/
│   │   │   ├── DocumentCard.vue
│   │   │   ├── DocumentList.vue
│   │   │   └── UploadModal.vue
│   │   └── common/
│   │       ├── Button.vue
│   │       ├── Input.vue
│   │       └── Modal.vue
│   │
│   ├── composables/      # Composition API reusable logic
│   │   ├── useAuth.js
│   │   ├── useChat.js
│   │   ├── useWebSocket.js
│   │   └── useNotification.js
│   │
│   ├── layouts/          # Layout components
│   │   ├── DefaultLayout.vue
│   │   └── AuthLayout.vue
│   │
│   ├── router/           # Vue Router configuration
│   │   └── index.js
│   │
│   ├── stores/           # Pinia stores
│   │   ├── auth.js
│   │   ├── chat.js
│   │   └── documents.js
│   │
│   ├── utils/            # Utility functions
│   │   ├── api.js        # Axios instance and interceptors
│   │   ├── auth.js       # Auth helpers
│   │   ├── storage.js    # LocalStorage wrapper
│   │   └── validators.js # Form validators
│   │
│   ├── views/            # Page components (routes)
│   │   ├── Home.vue
│   │   ├── Login.vue
│   │   ├── Register.vue
│   │   ├── Chat.vue
│   │   ├── Documents.vue
│   │   └── Settings.vue
│   │
│   ├── App.vue           # Root component
│   └── main.js           # Application entry point
│
├── .env.example          # Environment variables template
├── .eslintrc.js          # ESLint configuration
├── .prettierrc           # Prettier configuration
├── index.html            # HTML entry point
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
└── tailwind.config.js    # Tailwind CSS configuration
```

### Backend Structure

```
backend/
├── app/
│   ├── core/             # Core functionality
│   │   ├── __init__.py
│   │   ├── main.py       # FastAPI app instance
│   │   ├── config.py     # Configuration management
│   │   ├── database.py   # Database connection
│   │   ├── security.py   # Security utilities
│   │   └── dependencies.py # Dependency injection
│   │
│   ├── models/           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── document.py
│   │
│   ├── schemas/          # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── document.py
│   │
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── custom_rag.py # RAG system
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   └── document_service.py
│   │
│   ├── api/              # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── documents.py
│   │
│   └── utils/            # Utilities
│       ├── __init__.py
│       ├── encryption.py
│       ├── validators.py
│       └── helpers.py
│
├── tests/                # Test files
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures
│   ├── test_auth.py
│   ├── test_chat.py
│   └── test_documents.py
│
├── data/                 # Data storage
│   ├── database.db       # SQLite database
│   └── documents/        # Uploaded documents
│
├── logs/                 # Log files
│   ├── app.log
│   └── error.log
│
├── .env.example          # Environment template
├── main.py               # Entry point
├── requirements.txt      # Python dependencies
└── pytest.ini            # Pytest configuration
```

---

## Coding Standards

### Frontend Standards

#### Vue Component Structure

```vue
<template>
  <!-- Template goes here -->
  <div class="component-name">
    <!-- Use semantic HTML -->
    <!-- Keep template clean and readable -->
  </div>
</template>

<script setup>
// 1. Imports
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// 2. Props
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  count: {
    type: Number,
    default: 0
  }
})

// 3. Emits
const emit = defineEmits(['update', 'delete'])

// 4. Composables
const router = useRouter()

// 5. Reactive state
const isLoading = ref(false)
const items = ref([])

// 6. Computed properties
const totalCount = computed(() => items.value.length)

// 7. Methods
const handleUpdate = () => {
  emit('update', items.value)
}

// 8. Lifecycle hooks
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* Component-specific styles */
/* Use Tailwind utility classes when possible */
/* Only add custom CSS when necessary */
</style>
```

#### JavaScript/Vue Style Guide

```javascript
// Use const and let, never var
const API_URL = 'http://localhost:8000'
let counter = 0

// Use arrow functions
const fetchData = async () => {
  const response = await api.get('/data')
  return response.data
}

// Use destructuring
const { id, name } = user
const [first, second] = items

// Use template literals
const message = `Hello, ${userName}!`

// Use async/await over promises
async function loadUser(id) {
  try {
    const user = await api.get(`/users/${id}`)
    return user
  } catch (error) {
    console.error('Failed to load user:', error)
    throw error
  }
}

// Naming conventions
const userName = 'John'          // camelCase for variables
const MAX_RETRIES = 3            // UPPER_CASE for constants
function calculateTotal() {}      // camelCase for functions
class UserService {}             // PascalCase for classes
```

#### Component Naming

```javascript
// Use PascalCase for component names
// ✅ Good
ChatMessage.vue
DocumentList.vue
UserProfile.vue

// ❌ Bad
chatMessage.vue
document-list.vue
userprofile.vue

// Use multi-word names (avoid single-word components)
// ✅ Good
UserCard.vue
MessageList.vue

// ❌ Bad
User.vue
List.vue
```

### Backend Standards

#### Python Style Guide (PEP 8)

```python
# Use snake_case for functions and variables
def calculate_total_price(items):
    total_price = 0
    return total_price

# Use PascalCase for classes
class UserService:
    def __init__(self):
        self.users = []

# Use UPPER_CASE for constants
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
API_VERSION = "v1"

# Type hints
def get_user(user_id: int) -> dict:
    """Get user by ID."""
    return database.get(user_id)

# Docstrings
def process_document(file_path: str, user_id: int) -> dict:
    """
    Process uploaded document and extract content.

    Args:
        file_path: Path to the uploaded file
        user_id: ID of the user who uploaded the file

    Returns:
        Dictionary containing document metadata

    Raises:
        ValueError: If file format is not supported
        IOError: If file cannot be read
    """
    pass
```

#### FastAPI Endpoint Structure

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response.

    - **message**: The user's message
    - **conversation_id**: Optional conversation ID to continue
    - **use_rag**: Whether to use RAG system (default: true)
    """
    try:
        service = ChatService(db)
        response = await service.process_message(
            message=request.message,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            use_rag=request.use_rag
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )
```

---

## Git Workflow

### Branch Strategy

We follow **Git Flow** branching model:

```
main (production)
├── develop (integration)
│   ├── feature/user-authentication
│   ├── feature/document-upload
│   ├── feature/rag-system
│   ├── bugfix/chat-scroll-issue
│   └── hotfix/security-patch
```

### Branch Naming

```bash
# Features
feature/user-authentication
feature/document-management
feature/rag-integration

# Bug fixes
bugfix/login-error
bugfix/upload-validation

# Hotfixes (urgent production fixes)
hotfix/security-vulnerability
hotfix/database-connection

# Releases
release/v1.0.0
release/v1.1.0
```

### Commit Messages

Follow **Conventional Commits** specification:

```bash
# Format
<type>(<scope>): <subject>

<body>

<footer>

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation changes
style:    Code style changes (formatting, no logic change)
refactor: Code refactoring
test:     Adding or updating tests
chore:    Maintenance tasks

# Examples
feat(auth): add JWT token refresh endpoint

fix(chat): resolve message scroll issue on mobile

docs(api): update authentication documentation

refactor(rag): optimize embedding generation performance

test(documents): add unit tests for upload validation

chore(deps): update dependencies to latest versions
```

### Git Commands

```bash
# Create new feature branch
git checkout -b feature/my-feature develop

# Make changes and commit
git add .
git commit -m "feat(feature): add new functionality"

# Keep branch up to date
git checkout develop
git pull origin develop
git checkout feature/my-feature
git rebase develop

# Push to remote
git push origin feature/my-feature

# Create pull request on GitHub

# After PR is merged
git checkout develop
git pull origin develop
git branch -d feature/my-feature
```

### Pull Request Guidelines

**PR Title:**
```
feat(auth): Implement JWT token refresh mechanism
```

**PR Description Template:**
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Related Issues
Closes #123
```

---

## Testing Guidelines

### Frontend Testing

#### Unit Tests (Vitest)

```javascript
// components/__tests__/ChatMessage.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from '../ChatMessage.vue'

describe('ChatMessage', () => {
  it('renders user message correctly', () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          role: 'user',
          content: 'Hello, world!'
        }
      }
    })

    expect(wrapper.text()).toContain('Hello, world!')
    expect(wrapper.classes()).toContain('user-message')
  })

  it('emits delete event when delete button is clicked', async () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: { role: 'user', content: 'Test' }
      }
    })

    await wrapper.find('.delete-btn').trigger('click')
    expect(wrapper.emitted('delete')).toBeTruthy()
  })
})
```

#### Component Tests

```javascript
// stores/__tests__/auth.spec.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('logs in user successfully', async () => {
    const store = useAuthStore()

    await store.login({
      email: 'test@example.com',
      password: 'password123'
    })

    expect(store.isAuthenticated).toBe(true)
    expect(store.user).not.toBeNull()
  })
})
```

#### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test ChatMessage.spec.js
```

### Backend Testing

#### Unit Tests (Pytest)

```python
# tests/test_auth.py
import pytest
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate

@pytest.fixture
def auth_service(db_session):
    return AuthService(db_session)

def test_create_user_success(auth_service):
    """Test successful user creation."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="SecurePass123!"
    )

    user = auth_service.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password != "SecurePass123!"

def test_create_user_duplicate_email(auth_service):
    """Test user creation with duplicate email."""
    user_data = UserCreate(
        email="existing@example.com",
        username="user1",
        password="Pass123!"
    )

    auth_service.create_user(user_data)

    with pytest.raises(ValueError, match="Email already exists"):
        auth_service.create_user(user_data)
```

#### Integration Tests

```python
# tests/test_api_chat.py
import pytest
from fastapi.testclient import TestClient
from app.core.main import app

client = TestClient(app)

@pytest.fixture
def authenticated_headers(test_user):
    """Get authentication headers."""
    response = client.post("/api/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_send_chat_message(authenticated_headers):
    """Test sending a chat message."""
    response = client.post(
        "/api/chat",
        json={
            "message": "What is RAG?",
            "use_rag": True
        },
        headers=authenticated_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "message_id" in data
```

#### Running Backend Tests

```bash
cd backend

# Activate virtual environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_create_user_success

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

---

## Debugging

### Frontend Debugging

#### Browser DevTools

```javascript
// Use console methods
console.log('Data:', data)
console.error('Error occurred:', error)
console.warn('Warning:', warning)
console.table(users)  // Display array/object as table

// Debug reactive state
import { watch } from 'vue'

watch(
  () => store.messages,
  (newVal, oldVal) => {
    console.log('Messages changed:', { newVal, oldVal })
  },
  { deep: true }
)
```

#### Vue DevTools

1. Install Vue DevTools browser extension
2. Open DevTools → Vue tab
3. Inspect components, Pinia stores, routes
4. Time-travel debugging for state changes

#### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Vue: Chrome",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/src",
      "sourceMapPathOverrides": {
        "webpack:///src/*": "${webRoot}/*"
      }
    }
  ]
}
```

### Backend Debugging

#### Python Debugger (pdb)

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint() in Python 3.7+
breakpoint()

# Commands:
# n - next line
# s - step into function
# c - continue execution
# p variable - print variable
# l - list code around current line
# q - quit debugger
```

#### VS Code Debugging

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
logger.critical("Critical error")

# Structured logging
logger.info(
    "User logged in",
    extra={
        "user_id": user.id,
        "ip_address": request.client.host
    }
)
```

---

## Common Issues

### Frontend Issues

#### Issue: "Module not found" error

```bash
# Solution 1: Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Solution 2: Check import path
# ✅ Correct
import { useAuthStore } from '@/stores/auth'

# ❌ Incorrect
import { useAuthStore } from '@/stores/auth.js'
```

#### Issue: CORS errors

```javascript
// Backend needs to allow frontend origin
// Check backend/.env
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

// Check browser console for actual origin
console.log(window.location.origin)
```

#### Issue: Pinia store not working

```javascript
// Make sure Pinia is installed
import { createPinia } from 'pinia'

const pinia = createPinia()
app.use(pinia)

// Use store in components
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
```

### Backend Issues

#### Issue: "ModuleNotFoundError"

```bash
# Solution 1: Check if in virtual environment
which python  # Should show venv path

# Solution 2: Reinstall dependencies
pip install -r requirements.txt

# Solution 3: Add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

#### Issue: Database locked error

```bash
# SQLite database is locked
# Solution: Close all connections
# Check for running processes using the database

# Windows
tasklist | findstr python
taskkill /PID <pid> /F

# Linux/Mac
ps aux | grep python
kill -9 <pid>
```

#### Issue: OpenAI API errors

```python
# Check API key
import os
print(os.getenv("OPENAI_API_KEY"))

# Check rate limits
# OpenAI has rate limits - implement retry logic

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_openai_api():
    # API call here
    pass
```

### Docker Issues

#### Issue: Container won't start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check environment variables
docker-compose exec backend env
```

---

## Best Practices

### Code Quality

```bash
# Frontend
npm run lint              # Check for linting errors
npm run lint:fix          # Auto-fix linting errors
npm run format            # Format code with Prettier

# Backend
pylint app/               # Check code quality
black app/                # Format code
mypy app/                 # Type checking
```

### Performance

**Frontend:**
- Use `v-show` for frequently toggled elements
- Use `v-if` for conditional rendering
- Lazy load routes and components
- Debounce user input
- Implement virtual scrolling for long lists

```javascript
// Debounce example
import { debounce } from 'lodash-es'

const search = debounce((query) => {
  api.search(query)
}, 300)
```

**Backend:**
- Use async/await for I/O operations
- Implement database connection pooling
- Cache frequently accessed data
- Use database indexes
- Paginate large result sets

### Security

**Frontend:**
- Never store sensitive data in localStorage
- Sanitize user input
- Use HTTPS in production
- Implement CSRF protection
- Validate all user input

**Backend:**
- Never log sensitive data (passwords, tokens)
- Use parameterized queries (SQLAlchemy ORM)
- Implement rate limiting
- Validate and sanitize all input
- Use secure password hashing (bcrypt)
- Keep dependencies updated

```python
# ✅ Good - Parameterized query
user = db.query(User).filter(User.email == email).first()

# ❌ Bad - SQL injection vulnerability
query = f"SELECT * FROM users WHERE email = '{email}'"
```

---

## Contributing

### Before Submitting PR

```bash
# 1. Update from develop
git checkout develop
git pull origin develop

# 2. Rebase your branch
git checkout feature/my-feature
git rebase develop

# 3. Run tests
# Frontend
cd frontend && npm run test && npm run lint
# Backend
cd backend && pytest && pylint app/

# 4. Update documentation if needed

# 5. Push and create PR
git push origin feature/my-feature
```

### Code Review Checklist

**For Reviewers:**
- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance considerations addressed
- [ ] Error handling is proper
- [ ] Code is readable and maintainable

**For Authors:**
- [ ] PR description is clear and complete
- [ ] All tests pass locally
- [ ] Code is self-documented
- [ ] No console.log or debug statements
- [ ] Commits are clean and descriptive

---

## Additional Resources

### Documentation

- [Vue 3 Documentation](https://vuejs.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

### Tools

- [Vue DevTools](https://devtools.vuejs.org/)
- [Postman](https://www.postman.com/) - API testing
- [DBeaver](https://dbeaver.io/) - Database client

### Community

- [Vue Discord](https://discord.com/invite/vue)
- [FastAPI Discord](https://discord.gg/fastapi)
- Stack Overflow with tags: `vue.js`, `fastapi`, `python`

---

## Need Help?

- Check the [API Documentation](../api/)
- Review [Architecture Documentation](../architecture/)
- Open an issue on GitHub
- Contact the development team

---

**Happy Coding!** 🚀

**Last Updated:** 2025-12-05
