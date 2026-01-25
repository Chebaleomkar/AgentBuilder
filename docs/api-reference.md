# API Reference

Complete reference for all AgentBuilder API endpoints.

**Base URL:** `http://localhost:8000/api/v1`

---

## 🤖 Agents

### List Agents

```http
GET /agents
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| status | string | Filter by status (active, inactive) |
| page | int | Page number (default: 1) |
| per_page | int | Items per page (default: 20, max: 100) |

**Response:**
```json
{
  "agents": [...],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

---

### Create Agent

```http
POST /agents
```

**Body:**
```json
{
  "name": "Research Agent",
  "role": "Research Specialist",
  "goal": "Find and analyze information",
  "instructions": "Search the web thoroughly...",
  "model": "gpt-4",
  "temperature": 0.7,
  "tools": ["web_search", "text_summarizer"],
  "memory_type": "session"
}
```

**Required Fields:** `name`, `role`

**Response:** `201 Created`
```json
{
  "id": "agent_abc123",
  "name": "Research Agent",
  ...
}
```

---

### Get Agent

```http
GET /agents/{agent_id}
```

**Response:** `200 OK`
```json
{
  "id": "agent_abc123",
  "name": "Research Agent",
  "role": "Research Specialist",
  "model": "gpt-4",
  ...
}
```

---

### Update Agent

```http
PUT /agents/{agent_id}
```

**Body:** (partial update allowed)
```json
{
  "temperature": 0.5,
  "tools": ["web_search"]
}
```

---

### Delete Agent

```http
DELETE /agents/{agent_id}
```

**Response:** `200 OK`
```json
{"message": "Agent deleted successfully"}
```

---

### Execute Agent

```http
POST /agents/{agent_id}/execute
```

**Body:**
```json
{
  "input": {
    "query": "Research AI browser automation"
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "exec_xyz789",
  "status": "completed",
  "output_data": {
    "result": {...},
    "raw_response": "...",
    "provider": "openai",
    "model": "gpt-4"
  },
  "token_usage": {
    "input_tokens": 450,
    "output_tokens": 380,
    "total_tokens": 830
  },
  "duration_ms": 3420,
  "steps": [...],
  "logs": [...]
}
```

---

## 🔄 Workflows

### List Workflows

```http
GET /workflows
```

### Create Workflow

```http
POST /workflows
```

**Body:**
```json
{
  "name": "Research Pipeline",
  "description": "Multi-agent research workflow",
  "coordination_strategy": "sequential",
  "agents": ["agent_1", "agent_2", "agent_3"]
}
```

**Coordination Strategies:**
- `sequential` - Run agents in order
- `supervisor` - First agent coordinates
- `peer` - Run all in parallel
- `conditional` - Branch based on conditions

### Execute Workflow

```http
POST /workflows/{workflow_id}/execute
```

**Body:**
```json
{
  "input": {
    "task": "Analyze the AI market"
  }
}
```

---

## 🛠️ Tools

### List Tools

```http
GET /tools
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| category | string | Filter by category |
| include_builtin | bool | Include built-in tools (default: true) |

**Response:**
```json
{
  "tools": [
    {
      "id": "tool_web_search",
      "name": "web_search",
      "description": "Search the web for information",
      "category": "web",
      "is_builtin": true,
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"}
        }
      }
    }
  ]
}
```

### Built-in Tools

```http
GET /tools/builtin
```

Returns only system-provided tools.

---

## 📊 Executions

### List Executions

```http
GET /executions
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| agent_id | string | Filter by agent |
| workflow_id | string | Filter by workflow |
| status | string | Filter by status |

### Get Execution Details

```http
GET /executions/{execution_id}
```

Returns full execution with steps and logs.

### Cancel Execution

```http
POST /executions/{execution_id}/cancel
```

Only works for `pending` or `running` executions.

### Get Execution Logs

```http
GET /executions/{execution_id}/logs
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| level | string | Filter by level (debug, info, warning, error) |

---

## 🎮 Demo Agents

Pre-built agents for testing.

### Research Agent

```http
POST /demo/research
```

**Body:**
```json
{
  "topic": "AI browser automation",
  "max_sources": 5
}
```

### Automation Agent

```http
POST /demo/automation
```

**Body:**
```json
{
  "data": [{"name": "item1"}, {"name": "item2"}],
  "task": "analyze"
}
```

### Multi-Agent Orchestrator

```http
POST /demo/multi-agent
```

**Body:**
```json
{
  "task": "Analyze the AI market",
  "context": {}
}
```

---

## 🔍 Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "app": "AgentBuilder",
  "version": "1.0.0"
}
```

---

## ⚠️ Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Check request body |
| 500 | Internal Error - Something broke |

---

## 📝 Pagination

List endpoints support pagination:

```http
GET /agents?page=2&per_page=10
```

Response includes:
```json
{
  "items": [...],
  "total": 42,
  "page": 2,
  "per_page": 10
}
```

---

*Next: [Development Guide →](./development-guide.md)*
