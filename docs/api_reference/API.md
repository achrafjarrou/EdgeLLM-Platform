# API Reference

## Base URL
```
http://localhost:8080
```

## Authentication
All endpoints require Bearer token:
```
Authorization: Bearer your-api-key
```

## Endpoints

### POST /v1/inference
Execute LLM inference

**Request:**
```json
{
  "prompt": "Your question here",
  "max_tokens": 1024,
  "temperature": 0.1,
  "tier": "standard"
}
```

**Response:**
```json
{
  "request_id": "abc123",
  "result": "Model response",
  "model_used": "phi4-mini-local",
  "latency_ms": 340.5,
  "cost_eur": 0.0,
  "data_location": "on-premise",
  "tokens": {
    "input": 25,
    "output": 150,
    "total": 175
  },
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### GET /v1/models
List available models for your tier

### GET /v1/usage
Get usage statistics

### GET /health
Health check endpoint
