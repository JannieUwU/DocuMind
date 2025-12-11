# API Documentation

Vue3 RAG Hybrid Search Application - API Reference

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

---

## Authentication Endpoints

### Register User

Register a new user account.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response:** `201 Created`
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2025-12-05T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `409 Conflict` - Email or username already exists

---

### Login

Authenticate and receive JWT tokens.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `404 Not Found` - User not found

---

### Refresh Token

Get a new access token using refresh token.

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Chat Endpoints

### Send Message

Send a chat message and get AI response.

**Endpoint:** `POST /api/chat`

**Authentication:** Required

**Request Body:**
```json
{
  "message": "What is RAG?",
  "conversation_id": "conv_123",
  "use_rag": true,
  "stream": false
}
```

**Parameters:**
- `message` (string, required) - The user's message
- `conversation_id` (string, optional) - Continue existing conversation
- `use_rag` (boolean, default: true) - Use RAG system for enhanced responses
- `stream` (boolean, default: false) - Enable streaming responses

**Response:** `200 OK`
```json
{
  "message_id": "msg_456",
  "conversation_id": "conv_123",
  "response": "RAG (Retrieval-Augmented Generation) is...",
  "sources": [
    {
      "document_id": "doc_789",
      "title": "RAG Introduction",
      "relevance_score": 0.95
    }
  ],
  "timestamp": "2025-12-05T10:35:00Z"
}
```

**Streaming Response:**

When `stream: true`, returns Server-Sent Events (SSE):

```
data: {"type": "token", "content": "RAG"}
data: {"type": "token", "content": " is"}
data: {"type": "token", "content": " a"}
data: {"type": "done", "message_id": "msg_456"}
```

---

### Get Conversation History

Retrieve chat history for a conversation.

**Endpoint:** `GET /api/chat/history/{conversation_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "conversation_id": "conv_123",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-12-05T10:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Hi! How can I help you?",
      "timestamp": "2025-12-05T10:30:01Z"
    }
  ],
  "created_at": "2025-12-05T10:30:00Z"
}
```

---

### List Conversations

Get all conversations for the authenticated user.

**Endpoint:** `GET /api/chat/conversations`

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, default: 20) - Number of conversations to return
- `offset` (integer, default: 0) - Pagination offset

**Response:** `200 OK`
```json
{
  "conversations": [
    {
      "id": "conv_123",
      "title": "RAG Discussion",
      "last_message": "RAG is a technique...",
      "message_count": 10,
      "updated_at": "2025-12-05T10:35:00Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

---

### Delete Conversation

Delete a conversation and all its messages.

**Endpoint:** `DELETE /api/chat/conversations/{conversation_id}`

**Authentication:** Required

**Response:** `204 No Content`

---

## Document Management

### Upload Document

Upload a document for RAG processing.

**Endpoint:** `POST /api/documents/upload`

**Authentication:** Required

**Request:** `multipart/form-data`

```
file: [PDF/TXT file]
title: (optional) Document title
tags: (optional) Comma-separated tags
```

**Response:** `201 Created`
```json
{
  "document_id": "doc_789",
  "title": "My Document.pdf",
  "size": 1048576,
  "status": "processing",
  "uploaded_at": "2025-12-05T10:40:00Z"
}
```

**Supported Formats:**
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)

**Limits:**
- Max file size: 10 MB
- Max files per user: 100

---

### List Documents

Get all documents for the authenticated user.

**Endpoint:** `GET /api/documents`

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, default: 20)
- `offset` (integer, default: 0)
- `status` (string) - Filter by status: processing, ready, failed

**Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "doc_789",
      "title": "My Document.pdf",
      "size": 1048576,
      "status": "ready",
      "uploaded_at": "2025-12-05T10:40:00Z"
    }
  ],
  "total": 5
}
```

---

### Get Document

Get details of a specific document.

**Endpoint:** `GET /api/documents/{document_id}`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "doc_789",
  "title": "My Document.pdf",
  "size": 1048576,
  "status": "ready",
  "chunks": 45,
  "tags": ["ai", "documentation"],
  "uploaded_at": "2025-12-05T10:40:00Z",
  "processed_at": "2025-12-05T10:41:00Z"
}
```

---

### Delete Document

Delete a document and remove it from the vector store.

**Endpoint:** `DELETE /api/documents/{document_id}`

**Authentication:** Required

**Response:** `204 No Content`

---

## User Profile

### Get Profile

Get the authenticated user's profile.

**Endpoint:** `GET /api/users/me`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2025-12-05T10:30:00Z",
  "document_count": 5,
  "conversation_count": 15
}
```

---

### Update Profile

Update user profile information.

**Endpoint:** `PATCH /api/users/me`

**Authentication:** Required

**Request Body:**
```json
{
  "username": "newusername",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`
```json
{
  "id": "user_123",
  "email": "newemail@example.com",
  "username": "newusername",
  "updated_at": "2025-12-05T10:50:00Z"
}
```

---

## Configuration

### Get User Configuration

Get RAG system configuration for the user.

**Endpoint:** `GET /api/config`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "search_k": 5,
  "embedding_model": "text-embedding-ada-002"
}
```

---

### Update Configuration

Update RAG system configuration.

**Endpoint:** `PUT /api/config`

**Authentication:** Required

**Request Body:**
```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "search_k": 5
}
```

**Response:** `200 OK`

---

## Health Check

### System Health

Check if the API is running.

**Endpoint:** `GET /health`

**Authentication:** Not required

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-05T10:55:00Z"
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limiting

- **Default limit:** 100 requests per minute per user
- **Document upload:** 10 uploads per hour per user
- **Chat messages:** 30 messages per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638720000
```

---

## Webhooks (Coming Soon)

Future support for webhooks to notify about:
- Document processing completion
- Long-running chat completions
- System updates

---

## SDKs

### Python SDK Example

```python
from rag_client import RAGClient

client = RAGClient(api_key="your_api_key")

# Send chat message
response = client.chat.send(
    message="What is RAG?",
    use_rag=True
)

# Upload document
document = client.documents.upload(
    file_path="document.pdf",
    title="My Document"
)
```

### JavaScript SDK Example

```javascript
import { RAGClient } from '@rag/client';

const client = new RAGClient({ apiKey: 'your_api_key' });

// Send chat message
const response = await client.chat.send({
  message: 'What is RAG?',
  useRag: true
});

// Upload document
const document = await client.documents.upload({
  file: fileBlob,
  title: 'My Document'
});
```

---

## Support

For API support and questions:
- Documentation: https://docs.your-domain.com
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@your-domain.com

---

**API Version:** 1.0.0
**Last Updated:** 2025-12-05
