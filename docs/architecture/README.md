# Architecture Documentation

**Project:** Vue3 RAG Hybrid Search Application
**Version:** 1.0.0
**Last Updated:** 2025-12-05

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [RAG System Design](#rag-system-design)
6. [Database Schema](#database-schema)
7. [Authentication Flow](#authentication-flow)
8. [Frontend Architecture](#frontend-architecture)
9. [Backend Architecture](#backend-architecture)
10. [Security Architecture](#security-architecture)
11. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The Vue3 RAG Hybrid Search Application is a full-stack web application that combines modern frontend technologies with advanced AI-powered search capabilities. The system uses Retrieval-Augmented Generation (RAG) to provide intelligent, context-aware responses by retrieving relevant information from a document knowledge base.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│                    (Vue 3 + Vite + Tailwind)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/HTTP
                             │ REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend Server                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Auth Module  │  │ Chat Module  │  │ Document Management  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
│         │                  │                     │              │
│         └──────────────────┼─────────────────────┘              │
│                            ▼                                    │
│                   ┌────────────────┐                            │
│                   │  RAG Engine    │                            │
│                   └────────┬───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌───────────────┐ ┌──────────┐ ┌────────────┐
     │   SQLite/     │ │  Vector  │ │  OpenAI    │
     │  PostgreSQL   │ │  Store   │ │    API     │
     │   Database    │ │ (FAISS)  │ │            │
     └───────────────┘ └──────────┘ └────────────┘
```

### Key Components

1. **Frontend (Vue 3)** - User interface for interaction
2. **Backend (FastAPI)** - RESTful API server
3. **RAG Engine** - Retrieval-Augmented Generation system
4. **Database** - User data and conversation storage
5. **Vector Store** - Document embeddings for semantic search
6. **OpenAI API** - Language model for generation

---

## Architecture Diagram

### System Context Diagram

```
                    ┌──────────────┐
                    │     User     │
                    └──────┬───────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Web Application      │
              │   (Vue3 Frontend)      │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   API Gateway          │
              │   (FastAPI Backend)    │
              └────┬────────────┬──────┘
                   │            │
        ┏━━━━━━━━━━┷━━━━━━┓    │
        ▼                  ▼    ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│   Database    │  │  RAG System  │  │  OpenAI API  │
│   (SQLite)    │  │   (Custom)   │  │   (GPT-4)    │
└───────────────┘  └──────────────┘  └──────────────┘
```

---

## Component Architecture

### Frontend Components

```
src/
├── App.vue                    # Root component
├── main.js                    # Application entry point
│
├── views/                     # Page-level components
│   ├── Login.vue             # Authentication page
│   ├── Chat.vue              # Main chat interface
│   ├── Documents.vue         # Document management
│   └── Settings.vue          # User settings
│
├── components/               # Reusable components
│   ├── ChatMessage.vue       # Single message component
│   ├── ChatInput.vue         # Message input box
│   ├── DocumentList.vue      # Document list display
│   ├── DocumentUpload.vue    # Upload interface
│   └── Sidebar.vue           # Navigation sidebar
│
├── stores/                   # Pinia state management
│   ├── auth.js              # Authentication state
│   ├── chat.js              # Chat state
│   └── documents.js         # Document state
│
├── router/                   # Vue Router
│   └── index.js             # Route configuration
│
└── utils/                    # Utility functions
    ├── api.js               # API client
    ├── auth.js              # Auth helpers
    └── storage.js           # Local storage
```

### Backend Components

```
backend/
├── main.py                   # Application entry point
│
├── app/
│   ├── core/                # Core functionality
│   │   ├── main.py         # FastAPI app instance
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database connection
│   │   ├── security.py     # Security utilities
│   │   └── dependencies.py # Dependency injection
│   │
│   ├── services/           # Business logic
│   │   ├── custom_rag.py   # RAG system implementation
│   │   ├── auth_service.py # Authentication logic
│   │   ├── chat_service.py # Chat logic
│   │   └── document_service.py # Document processing
│   │
│   ├── models/             # Database models
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── document.py
│   │
│   ├── schemas/            # Pydantic schemas
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── document.py
│   │
│   └── utils/              # Utility functions
│       ├── encryption.py
│       ├── validators.py
│       └── helpers.py
│
└── data/                   # Data storage
    ├── database.db         # SQLite database
    └── documents/          # Uploaded documents
```

---

## Data Flow

### Chat Message Flow

```
1. User Input
   │
   ▼
2. Frontend (Vue Component)
   │ - Validate input
   │ - Dispatch to store
   │
   ▼
3. API Request (Axios)
   │ POST /api/chat
   │ Headers: Authorization: Bearer <token>
   │ Body: { message, conversation_id, use_rag }
   │
   ▼
4. Backend API Endpoint
   │ - Verify JWT token
   │ - Validate request data
   │
   ▼
5. Chat Service
   │ - Load conversation history
   │ - Check RAG flag
   │
   ▼
6. RAG System (if enabled)
   │ - Generate query embedding
   │ - Search vector store
   │ - Retrieve relevant documents
   │ - Rank results
   │
   ▼
7. OpenAI API Call
   │ - Construct prompt with context
   │ - Call GPT-4 API
   │ - Stream or batch response
   │
   ▼
8. Database Storage
   │ - Save user message
   │ - Save AI response
   │ - Update conversation
   │
   ▼
9. API Response
   │ - Format response
   │ - Include sources
   │
   ▼
10. Frontend Update
    │ - Update chat store
    │ - Render new messages
    │ - Scroll to bottom
```

### Document Upload Flow

```
1. User Selects File
   │
   ▼
2. Frontend Validation
   │ - Check file type (PDF, TXT, MD)
   │ - Check file size (< 10MB)
   │
   ▼
3. Upload Request
   │ POST /api/documents/upload
   │ Content-Type: multipart/form-data
   │
   ▼
4. Backend Receives File
   │ - Validate file
   │ - Generate document ID
   │
   ▼
5. File Processing
   │ - Extract text content
   │ - Split into chunks
   │ - Generate embeddings
   │
   ▼
6. Vector Store Update
   │ - Store embeddings
   │ - Index for search
   │
   ▼
7. Database Update
   │ - Save document metadata
   │ - Link to user
   │
   ▼
8. Response to Frontend
   │ - Document ID
   │ - Processing status
```

---

## RAG System Design

### RAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG System                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            Query Processing                          │ │
│  │  • Query understanding                               │ │
│  │  • Query expansion                                   │ │
│  │  • Embedding generation                              │ │
│  └────────────────────┬─────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            Retrieval Engine                          │ │
│  │  • Vector similarity search (FAISS)                  │ │
│  │  • Keyword search (BM25)                             │ │
│  │  • Hybrid fusion                                     │ │
│  └────────────────────┬─────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            Re-ranking                                │ │
│  │  • Cross-encoder scoring                             │ │
│  │  • Result diversification                            │ │
│  │  • Top-k selection                                   │ │
│  └────────────────────┬─────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            Context Building                          │ │
│  │  • Assemble retrieved chunks                         │ │
│  │  • Add metadata                                      │ │
│  │  • Format for LLM                                    │ │
│  └────────────────────┬─────────────────────────────────┘ │
│                       │                                    │
└───────────────────────┼────────────────────────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │    LLM (GPT-4)   │
              │    Generation    │
              └──────────────────┘
```

### Embedding Strategy

- **Model**: OpenAI text-embedding-ada-002
- **Dimension**: 1536
- **Chunk Size**: 512 tokens with 50 token overlap
- **Metadata**: Document ID, title, page number, timestamp

### Hybrid Search Algorithm

1. **Vector Search** (70% weight)
   - Semantic similarity using cosine distance
   - Returns top 20 candidates

2. **Keyword Search** (30% weight)
   - BM25 algorithm for exact matches
   - Returns top 20 candidates

3. **Fusion**
   - Reciprocal Rank Fusion (RRF)
   - Combined score calculation
   - Top 5 results selected

4. **Re-ranking**
   - Cross-encoder model for final scoring
   - Relevance threshold filtering

---

## Database Schema

### User Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE
);
```

### Conversation Table

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Message Table

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources TEXT,  -- JSON array of source documents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
```

### Document Table

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',  -- 'processing', 'ready', 'failed'
    chunks INTEGER DEFAULT 0,
    tags TEXT,  -- JSON array
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│    User     │────1:N──│  Conversation    │────1:N──│   Message   │
│             │         │                  │         │             │
│ • id        │         │ • id             │         │ • id        │
│ • email     │         │ • user_id        │         │ • conv_id   │
│ • username  │         │ • title          │         │ • role      │
│ • password  │         │ • created_at     │         │ • content   │
│ • created   │         │ • updated_at     │         │ • sources   │
└──────┬──────┘         └──────────────────┘         └─────────────┘
       │
       │1:N
       │
       ▼
┌─────────────┐
│  Document   │
│             │
│ • id        │
│ • user_id   │
│ • title     │
│ • file_path │
│ • status    │
│ • chunks    │
└─────────────┘
```

---

## Authentication Flow

### Registration Flow

```
1. User submits registration form
   │ email, username, password
   │
   ▼
2. Frontend validation
   │ Email format, password strength
   │
   ▼
3. POST /api/auth/register
   │
   ▼
4. Backend validation
   │ Check email/username uniqueness
   │
   ▼
5. Password hashing
   │ bcrypt with salt
   │
   ▼
6. Create user record
   │ Insert into database
   │
   ▼
7. Return user data
   │ (without password)
```

### Login Flow

```
1. User submits credentials
   │ email, password
   │
   ▼
2. POST /api/auth/login
   │
   ▼
3. Verify credentials
   │ Compare hashed password
   │
   ▼
4. Generate tokens
   │ • Access token (1 hour)
   │ • Refresh token (7 days)
   │
   ▼
5. Return tokens
   │ { access_token, refresh_token }
   │
   ▼
6. Store in frontend
   │ • Access token in memory
   │ • Refresh token in localStorage
```

### Authentication Middleware

```
┌───────────────┐
│  API Request  │
└───────┬───────┘
        │
        ▼
┌──────────────────┐
│ Extract Token    │
│ from Header      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      ┌───────────────┐
│ Verify Token     │─NO──▶│ Return 401    │
│ Signature        │      │ Unauthorized  │
└────────┬─────────┘      └───────────────┘
         │YES
         ▼
┌──────────────────┐      ┌───────────────┐
│ Check Expiry     │─YES─▶│ Return 401    │
│                  │      │ Token Expired │
└────────┬─────────┘      └───────────────┘
         │NO (valid)
         ▼
┌──────────────────┐
│ Extract User ID  │
│ from Token       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Load User Data   │
│ from Database    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Proceed to       │
│ Route Handler    │
└──────────────────┘
```

---

## Frontend Architecture

### State Management (Pinia)

```javascript
// Auth Store
{
  state: {
    user: null,
    token: null,
    isAuthenticated: false
  },
  actions: {
    login(credentials),
    logout(),
    refreshToken()
  }
}

// Chat Store
{
  state: {
    conversations: [],
    currentConversation: null,
    messages: []
  },
  actions: {
    sendMessage(content),
    loadHistory(conversationId),
    createConversation()
  }
}

// Document Store
{
  state: {
    documents: [],
    uploadProgress: 0
  },
  actions: {
    uploadDocument(file),
    fetchDocuments(),
    deleteDocument(id)
  }
}
```

### Component Communication

```
App.vue
├── Router View
    │
    ├── Login.vue (Unauth)
    │   └── Emits: @login-success
    │
    └── MainLayout.vue (Auth)
        ├── Sidebar.vue
        │   ├── Reads: conversations (store)
        │   └── Emits: @conversation-select
        │
        └── ChatView.vue
            ├── Props: conversationId
            ├── ChatMessages.vue
            │   ├── Props: messages[]
            │   └── ChatMessage.vue (v-for)
            │       └── Props: message
            │
            └── ChatInput.vue
                ├── Emits: @send-message
                └── Actions: store.sendMessage()
```

---

## Backend Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│  (FastAPI Routes - HTTP Request Handling)               │
│  • Request validation                                   │
│  • Response formatting                                  │
│  • Error handling                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                          │
│  (Business Logic)                                       │
│  • AuthService                                          │
│  • ChatService                                          │
│  • DocumentService                                      │
│  • RAGService                                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Layer                             │
│  (Database Access - ORM)                                │
│  • User Model                                           │
│  • Conversation Model                                   │
│  • Document Model                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Database                               │
│  (SQLite / PostgreSQL)                                  │
└─────────────────────────────────────────────────────────┘
```

### Dependency Injection

```python
# Example: Chat endpoint with dependencies

@router.post("/chat")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag_system: RAGSystem = Depends(get_rag_system)
):
    # Dependencies automatically injected:
    # - current_user: Authenticated user from JWT
    # - db: Database session
    # - rag_system: RAG system instance

    result = await chat_service.process_message(
        request, current_user, db, rag_system
    )
    return result
```

---

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│            1. Transport Security (HTTPS)                │
│  • TLS 1.3                                              │
│  • Certificate validation                               │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            2. Authentication (JWT)                      │
│  • Token-based authentication                           │
│  • Refresh token rotation                               │
│  • Token expiry (1 hour access, 7 days refresh)         │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            3. Authorization (RBAC)                      │
│  • User owns resources                                  │
│  • Role-based permissions                               │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            4. Data Security                             │
│  • Password hashing (bcrypt)                            │
│  • API key encryption (AES-256)                         │
│  • Sensitive data masking in logs                       │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            5. Input Validation                          │
│  • Pydantic schemas                                     │
│  • SQL injection prevention (ORM)                       │
│  • XSS protection                                       │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            6. Rate Limiting                             │
│  • 100 requests/minute per user                         │
│  • 10 uploads/hour per user                             │
│  • 30 chat messages/minute                              │
└─────────────────────────────────────────────────────────┘
```

### Encryption Strategy

```
┌─────────────────────────────────────────┐
│         At Rest Encryption              │
│                                         │
│  • API Keys: AES-256-GCM                │
│  • Passwords: bcrypt (cost factor 12)   │
│  • Tokens: HMAC-SHA256 signature        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      In Transit Encryption              │
│                                         │
│  • HTTPS/TLS 1.3                        │
│  • Certificate pinning (production)     │
└─────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development Environment

```
Developer Machine
├── Frontend (npm run dev)
│   └── http://localhost:5173
│
└── Backend (uvicorn --reload)
    └── http://localhost:8000
```

### Production Environment (Docker)

```
┌────────────────────────────────────────────────────────┐
│                    Load Balancer                       │
│                  (nginx / Traefik)                     │
└──────────────┬─────────────────────┬───────────────────┘
               │                     │
               ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  Frontend        │  │  Frontend        │
    │  Container       │  │  Container       │
    │  (nginx:alpine)  │  │  (nginx:alpine)  │
    └──────────────────┘  └──────────────────┘
               │                     │
               └──────────┬──────────┘
                          │
                          ▼
    ┌───────────────────────────────────────┐
    │         Backend Container             │
    │    (python:3.11-slim + FastAPI)       │
    └──────────────┬────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌────────────┐
│PostgreSQL│ │  Redis   │ │   S3 /     │
│Container │ │ Container│ │  Storage   │
└──────────┘ └──────────┘ └────────────┘
```

### Scaling Strategy

**Horizontal Scaling:**
- Multiple frontend containers behind load balancer
- Multiple backend containers with shared database
- Database read replicas for query load

**Vertical Scaling:**
- Increase container resources (CPU, RAM)
- Optimize database queries and indexes
- Cache frequently accessed data

**Caching Layers:**
```
Client
  └─► Browser Cache (Static assets)
       └─► CDN (Global distribution)
            └─► Redis Cache (API responses)
                 └─► Database
```

---

## Performance Considerations

### Frontend Optimization

- **Code Splitting**: Lazy loading routes and components
- **Asset Optimization**: Compressed images, minified JS/CSS
- **Caching**: Service worker for offline support
- **Virtual Scrolling**: For long message lists

### Backend Optimization

- **Connection Pooling**: Database connection reuse
- **Query Optimization**: Indexed columns, efficient joins
- **Async Operations**: Non-blocking I/O for AI API calls
- **Caching**: Redis for session data and frequent queries

### RAG System Optimization

- **Index Optimization**: FAISS index tuning
- **Batch Processing**: Bulk embedding generation
- **Result Caching**: Cache search results for common queries
- **Model Selection**: Balance between speed and accuracy

---

## Monitoring and Observability

### Logging Strategy

```
Application Logs
├── app.log (INFO level and above)
│   • Request/response logs
│   • Business logic events
│   • Performance metrics
│
└── error.log (ERROR level)
    • Exception stack traces
    • Critical failures
    • Security events
```

### Metrics to Monitor

- **Application**: Request rate, response time, error rate
- **Database**: Query time, connection pool usage, slow queries
- **RAG System**: Embedding generation time, search latency, relevance scores
- **Infrastructure**: CPU usage, memory usage, disk I/O, network throughput

### Health Checks

```
GET /health
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "vector_store": "ok",
    "openai_api": "ok"
  },
  "version": "1.0.0",
  "uptime": "3d 14h 22m"
}
```

---

## Future Enhancements

### Planned Improvements

1. **Multi-tenancy**: Support for organizational accounts
2. **Real-time Collaboration**: Multiple users in same chat
3. **Advanced Analytics**: Usage dashboards and insights
4. **Custom Models**: Support for local LLMs (Llama, Mistral)
5. **Mobile App**: Native iOS/Android applications
6. **Voice Interface**: Speech-to-text and text-to-speech
7. **Plugin System**: Extensible architecture for custom tools
8. **Webhooks**: Event notifications for integrations

---

**Architecture Version:** 1.0.0
**Last Updated:** 2025-12-05
**Maintained By:** Development Team
