# 🚀 AI Stack API Documentation

This document provides comprehensive API documentation for the AI Stack deployment, including all service endpoints, authentication methods, and usage examples.

## 📋 Table of Contents

- [Overview](#-overview)
- [Authentication](#-authentication)
- [Service APIs](#-service-apis)
- [Monitoring APIs](#-monitoring-apis)
- [Database APIs](#-database-apis)
- [WebSocket Endpoints](#-websocket-endpoints)
- [Health Check Endpoints](#-health-check-endpoints)
- [Error Handling](#-error-handling)
- [Rate Limiting](#-rate-limiting)
- [Examples](#-examples)

## 🎯 Overview

The AI Stack provides RESTful APIs for all services, with consistent authentication and error handling patterns. All APIs are secured behind the Nginx reverse proxy with SSL/TLS termination.

### Base URLs

- **Production**: `https://your-domain.com/`
- **Development**: `https://localhost/`
- **All Access**: Secured through Nginx reverse proxy with SSL/TLS

### Content Types

- **Request**: `application/json` (unless specified otherwise)
- **Response**: `application/json`
- **Encoding**: UTF-8

## 🔐 Authentication

### HTTP Basic Authentication

Most services use HTTP Basic Authentication through the reverse proxy:

```bash
# Format: username:password (base64 encoded)
Authorization: Basic <base64-encoded-credentials>

# Example - Monitoring Dashboard
curl -u "admin:password" https://localhost/monitoring/

# Example - Database Admin (Adminer)
curl -u "dbadmin:secure-password" https://localhost/adminer/
```

### Service-Specific Authentication

Some services have additional authentication layers:

- **Dify**: Built-in user authentication
- **OpenWebUI**: Built-in user authentication
- **N8N**: HTTP Basic + built-in auth
- **Flowise**: Built-in user authentication
- **LiteLLM**: API key authentication

```bash
# Header format
Authorization: Bearer <api-key>
X-API-Key: <api-key>

# Example
curl -H "Authorization: Bearer sk-1234" https://localhost/litellm/chat/completions
```

### Service-Specific Authentication

| Service | Method | Header | Example |
|---------|--------|--------|---------|
| **Monitoring** | HTTP Basic | `Authorization: Basic` | `admin:password` |
| **OpenWebUI** | HTTP Basic | `Authorization: Basic` | `user:password` |
| **N8N** | HTTP Basic | `Authorization: Basic` | `admin:password` |
| **Flowise** | HTTP Basic | `Authorization: Basic` | `admin:password` |
| **LiteLLM** | API Key | `Authorization: Bearer` | `sk-1234` |
| **Dify** | API Key | `Authorization: Bearer` | `app-1234` |

## 🤖 Service APIs

### Ollama API

Local LLM inference service.

**Base URL**: `https://localhost/ollama/`

#### Generate Completion

```http
POST /api/generate
```

**Request Body**:
```json
{
  "model": "llama3.2",
  "prompt": "Hello, how are you?",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9
  }
}
```

**Response**:
```json
{
  "model": "llama3.2",
  "created_at": "2024-01-01T00:00:00Z",
  "response": "Hello! I'm doing well, thank you for asking.",
  "done": true,
  "context": [1, 2, 3, ...],
  "total_duration": 1234567890,
  "load_duration": 123456,
  "prompt_eval_count": 10,
  "eval_count": 50,
  "eval_duration": 1234567890
}
```

#### List Models

```http
GET /api/tags
```

**Response**:
```json
{
  "models": [
    {
      "name": "llama3.2:latest",
      "size": 3826793672,
      "digest": "sha256:...",
      "details": {
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "3.2B",
        "quantization_level": "Q4_0"
      },
      "modified_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Pull Model

```http
POST /api/pull
```

**Request Body**:
```json
{
  "name": "llama3.2"
}
```

### LiteLLM API

LLM API proxy and load balancer. Compatible with OpenAI API format.

**Base URL**: `https://localhost/litellm/` or `http://localhost:4000/`

#### Chat Completions

```http
POST /chat/completions
```

**Headers**:
```
Authorization: Bearer sk-1234
Content-Type: application/json
```

**Request Body**:
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 100
}
```

**Claude Example**:
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 100
}
```

**Response**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### Models List

```http
GET /models
```

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    },
    {
      "id": "claude-3-5-sonnet-20241022",
      "object": "model",
      "created": 1727126400,
      "owned_by": "anthropic"
    }
  ]
}
```

### Dify API

AI application development platform.

**Base URL**: `https://localhost/dify/` or `http://localhost:3000/`

#### Create Chat Application

```http
POST /console/api/apps
```

**Headers**:
```
Authorization: Bearer app-1234
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "My Chat App",
  "mode": "chat",
  "model_config": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
}
```

#### Chat Message

```http
POST /v1/chat-messages
```

**Request Body**:
```json
{
  "query": "Hello, how are you?",
  "conversation_id": "conv-123",
  "user": "user-123",
  "inputs": {}
}
```

### N8N API

Workflow automation platform.

**Base URL**: `https://localhost/n8n/` or `http://localhost:5678/`

#### List Workflows

```http
GET /rest/workflows
```

**Response**:
```json
{
  "data": [
    {
      "id": "workflow-123",
      "name": "My Workflow",
      "active": true,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "nextCursor": null
}
```

#### Execute Workflow

```http
POST /webhook/workflow-123
```

**Request Body**:
```json
{
  "data": {
    "input": "Hello World"
  }
}
```

### Flowise API

Low-code AI workflow builder.

**Base URL**: `https://localhost/flowise/` or `http://localhost:3001/`

#### Create Chatflow

```http
POST /api/v1/chatflows
```

**Request Body**:
```json
{
  "name": "My Chatflow",
  "type": "chat",
  "nodes": [],
  "edges": []
}
```

#### Run Chatflow

```http
POST /api/v1/prediction/chatflow-123
```

**Request Body**:
```json
{
  "question": "Hello, how are you?",
  "overrideConfig": {}
}
```

### OpenWebUI API

Modern web interface for LLMs.

**Base URL**: `https://localhost/openwebui/` or `http://localhost:3002/`

#### List Models

```http
GET /api/models
```

**Response**:
```json
{
  "models": [
    {
      "id": "llama3.2",
      "name": "Llama 3.2",
      "object": "model"
    }
  ]
}
```

#### Chat Completion

```http
POST /api/chat/completions
```

**Request Body**:
```json
{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}
```

### Qdrant API

Vector database for embeddings.

**Base URL**: `https://localhost/qdrant/` or `http://localhost:6333/`

#### Create Collection

```http
PUT /collections/my-collection
```

**Request Body**:
```json
{
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

#### Search Vectors

```http
POST /collections/my-collection/points/search
```

**Request Body**:
```json
{
  "vector": [0.1, 0.2, 0.3, ...],
  "limit": 10,
  "with_payload": true
}
```

### OpenMemory API

AI memory management service.

**Base URL**: `https://localhost/openmemory/` or `http://localhost:8080/`

#### Add Memory

```http
POST /v1/memories/
```

**Request Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "My name is John"
    }
  ],
  "user_id": "user-123"
}
```

#### Get Memories

```http
GET /v1/memories/?user_id=user-123
```

## 📊 Monitoring APIs

### Health Status API

**Base URL**: `https://localhost/monitoring/`

#### Get All Services Status

```http
GET /
```

**Response**:
```json
{
  "dify-api": {
    "name": "Dify API",
    "status": "up",
    "response_time": 245,
    "error": null
  },
  "ollama": {
    "name": "Ollama",
    "status": "up",
    "response_time": 12,
    "error": null
  }
}
```

#### Get Service Logs

```http
GET /logs/{service-name}
```

**Response**:
```json
{
  "service_name": "dify-api",
  "service_info": {
    "name": "Dify API",
    "url": "http://dify-api:8080/health"
  },
  "logs": [
    "2024-01-01 00:00:00 INFO Starting Dify API server",
    "2024-01-01 00:00:01 INFO Database connected",
    "2024-01-01 00:00:02 INFO Server listening on port 8080"
  ]
}
```

#### Get Resource Usage

```http
GET /resources
```

**Response**:
```json
{
  "dify-api": {
    "name": "Dify API",
    "cpu_percent": 5.2,
    "memory_usage": 104857600,
    "memory_limit": 2147483648,
    "memory_percent": 4.9,
    "network_rx": 1024000,
    "network_tx": 512000,
    "disk_read": 0,
    "disk_write": 1024000,
    "container_status": "running",
    "container_id": "abc123"
  }
}
```

## 🗄️ Database APIs

### PostgreSQL (via Supabase)

**Base URL**: `https://localhost/supabase/` or `http://localhost:8000/`

#### REST API

```http
GET /rest/v1/table-name
POST /rest/v1/table-name
PATCH /rest/v1/table-name?id=eq.123
DELETE /rest/v1/table-name?id=eq.123
```

**Headers**:
```
apikey: your-anon-key
Authorization: Bearer your-service-role-key
Content-Type: application/json
```

### Redis

**Base URL**: `redis://redis:6379`

Redis is accessed programmatically or via Redis CLI:

```bash
# Connect to Redis
docker exec -it ai-stack-redis-1 redis-cli -a your-password

# Basic operations
SET key "value"
GET key
EXPIRE key 3600
```

## 🔌 WebSocket Endpoints

### N8N WebSocket

**URL**: `wss://localhost/n8n/`

Used for real-time workflow execution monitoring.

### LiteLLM Streaming

**URL**: `wss://localhost/litellm/`

Used for streaming chat completions.

```javascript
const ws = new WebSocket('wss://localhost/litellm/chat/completions');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.choices[0].delta.content);
};
```

## 🏥 Health Check Endpoints

All services provide health check endpoints:

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| **Dify API** | `GET /health` | `{"status": "ok"}` |
| **Dify Web** | `GET /health` | `{"status": "healthy"}` |
| **Ollama** | `GET /api/version` | `{"version": "0.1.0"}` |
| **LiteLLM** | `GET /health` | `{"status": "healthy"}` |
| **N8N** | `GET /healthz` | `ok` |
| **Flowise** | `GET /api/v1/health` | `ok` |
| **OpenWebUI** | `GET /health` | `OK` |
| **Qdrant** | `GET /health` | `ok` |
| **OpenMemory** | `GET /docs` | HTML API Documentation |
| **PostgreSQL** | `GET /health` | Database connection status |
| **Redis** | `GET /health` | PONG |

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "specific_field",
      "reason": "validation_reason"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req-123"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Service-Specific Errors

#### Ollama Errors

```json
{
  "error": "model 'unknown-model' not found, try pulling it first"
}
```

#### LiteLLM Errors

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": 401
  }
}
```

## 🚦 Rate Limiting

### Global Rate Limits

- **Authenticated Requests**: 1000 requests/minute per user
- **Anonymous Requests**: 100 requests/minute per IP
- **File Uploads**: 10 MB per request, 100 MB/hour per user

### Service-Specific Limits

| Service | Limit | Window |
|---------|-------|--------|
| **Ollama** | 50 requests/minute | Per IP |
| **LiteLLM** | 1000 tokens/minute | Per API key |
| **Dify** | 100 requests/minute | Per user |
| **N8N** | 500 executions/hour | Per workflow |
| **Qdrant** | 1000 requests/minute | Per collection |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## 💡 Examples

### Complete AI Chat Application

```python
import requests

# 1. Check service health
health = requests.get('https://localhost/monitoring/')
print("Services status:", health.json())

# 2. Generate text with Ollama
ollama_response = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.2",
    "prompt": "Write a Python function to calculate fibonacci numbers",
    "stream": False
})
print("Ollama response:", ollama_response.json()['response'])

# 3. Use LiteLLM for structured response
litellm_response = requests.post('http://localhost:4000/chat/completions',
    headers={'Authorization': 'Bearer sk-1234'},
    json={
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Format this as clean Python code"}],
        "temperature": 0.1
    }
)
print("Structured response:", litellm_response.json()['choices'][0]['message']['content'])
```

### Workflow Automation with N8N

```javascript
// Create a workflow via N8N API
const workflow = {
  name: "AI Content Processor",
  nodes: [
    {
      id: "webhook",
      type: "n8n-nodes-base.webhook",
      parameters: { httpMethod: "POST" }
    },
    {
      id: "ollama",
      type: "n8n-nodes-base.httpRequest",
      parameters: {
        url: "http://ollama:11434/api/generate",
        method: "POST",
        body: {
          model: "llama3.2",
          prompt: "{{$node.webhook.json.input}}"
        }
      }
    }
  ],
  connections: {
    "webhook": { main: [[{ node: "ollama", type: "main", index: 0 }]] }
  }
};

fetch('https://localhost/n8n/rest/workflows', {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + btoa('admin:password'),
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(workflow)
});
```

### Vector Search with Qdrant

```python
import requests

# Create collection
requests.put('http://localhost:6333/collections/documents',
    json={
        "vectors": {
            "size": 384,
            "distance": "Cosine"
        }
    }
)

# Add documents
requests.put('http://localhost:6333/collections/documents/points',
    json={
        "points": [
            {
                "id": 1,
                "vector": [0.1, 0.2, 0.3],  # Your embedding vector
                "payload": {"text": "Your document text"}
            }
        ]
    }
)

# Search similar documents
results = requests.post('http://localhost:6333/collections/documents/points/search',
    json={
        "vector": [0.1, 0.2, 0.3],  # Query embedding
        "limit": 5,
        "with_payload": True
    }
)
print("Search results:", results.json())
```

---

## 📞 Support

- **API Issues**: Check service logs via monitoring dashboard
- **Authentication Problems**: Verify credentials in `.env`
- **Rate Limiting**: Check `X-RateLimit-*` headers
- **Service Unavailable**: Use health check endpoints

For more detailed documentation, visit the individual service documentation links in the main README.</content>
<parameter name="filePath">/home/steelburn/Development/ai-stack-build/API_DOCUMENTATION.md