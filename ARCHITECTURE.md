# AgentBuilder - Architecture Documentation

## Overview

AgentBuilder is a UI-first AI agent platform built on top of the open-source [agenticaiframework](https://github.com/isathish/agenticaiframework). It provides a clean abstraction layer that converts UI configurations into executable agent definitions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AgentBuilder Platform                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js + TypeScript)                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Agent Builder│ │  Workflow    │ │  Playground  │ │   Logs &     │       │
│  │     UI       │ │  Designer    │ │  Execution   │ │  Monitoring  │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Python)                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  Agent API   │ │ Workflow API │ │  Tool API    │ │  Logs API    │       │
│  │  /agents/*   │ │ /workflows/* │ │  /tools/*    │ │  /logs/*     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Platform Services Layer                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │   Execution  │ │   Memory     │ │    Tool      │ │ Observability│       │
│  │    Engine    │ │   Service    │ │  Registry    │ │   Service    │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
├─────────────────────────────────────────────────────────────────────────────┤
│  agenticaiframework (Foundation)                                             │
│  Agent, OrchestrationEngine, AgentTeam, MemoryManagers, ToolRegistry        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
AgentBuilder/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API Routes
│   │   │   ├── agents.py      # Agent CRUD & execution
│   │   │   ├── workflows.py   # Workflow management
│   │   │   ├── tools.py       # Tool registry API
│   │   │   ├── logs.py        # Execution logs
│   │   │   └── users.py       # User management
│   │   ├── core/              # Core configurations
│   │   │   ├── config.py      # App settings
│   │   │   └── database.py    # Database connection
│   │   ├── models/            # Pydantic models
│   │   │   ├── agent.py       # Agent schemas
│   │   │   ├── workflow.py    # Workflow schemas
│   │   │   └── execution.py   # Execution schemas
│   │   ├── services/          # Business logic
│   │   │   ├── agent_service.py
│   │   │   ├── workflow_service.py
│   │   │   ├── tool_service.py
│   │   │   ├── memory_service.py
│   │   │   └── execution_service.py
│   │   └── engine/            # Execution engine
│   │       ├── executor.py    # Agent executor
│   │       └── orchestrator.py # Multi-agent orchestrator
│   ├── tools/                 # Custom tools
│   │   ├── web_search.py
│   │   ├── rag_tool.py
│   │   ├── file_reader.py
│   │   └── api_caller.py
│   ├── demo_agents/           # Pre-built demo agents
│   │   ├── research_agent.py
│   │   ├── automation_agent.py
│   │   └── multi_agent_orchestrator.py
│   ├── main.py                # FastAPI app entry
│   └── requirements.txt
│
├── frontend/                   # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx           # Home/Dashboard
│   │   ├── agents/
│   │   │   ├── page.tsx       # Agent list
│   │   │   ├── create/page.tsx # Agent builder
│   │   │   └── [id]/page.tsx  # Agent details
│   │   ├── workflows/
│   │   │   ├── page.tsx       # Workflow list
│   │   │   └── create/page.tsx # Workflow builder
│   │   ├── playground/
│   │   │   └── page.tsx       # Execution playground
│   │   └── logs/
│   │       └── page.tsx       # Logs & monitoring
│   ├── components/
│   │   ├── agent/             # Agent components
│   │   ├── workflow/          # Workflow components
│   │   ├── execution/         # Execution components
│   │   └── ui/                # Shared UI components
│   ├── lib/
│   │   ├── api.ts             # API client
│   │   └── types.ts           # TypeScript types
│   └── styles/
│       └── globals.css
│
└── docs/
    ├── ARCHITECTURE.md        # This file
    └── README.md              # Project README
```

## UI → agenticaiframework Mapping

### Agent Configuration Mapping

| UI Field | agenticaiframework Construct |
|----------|------------------------------|
| Name | `Agent.name` |
| Role | `Agent.role` |
| Goal/Instructions | `Agent.config["system_prompt"]` |
| Model Selection | `Agent.config["model"]` |
| Temperature | `Agent.config["temperature"]` |
| Tools | `Agent.capabilities` |
| Memory Type | `AgentMemoryManager` / `WorkflowMemoryManager` |

### Workflow Configuration Mapping

| UI Concept | Framework Construct |
|------------|---------------------|
| Multi-Agent Team | `AgentTeam` |
| Coordinator Strategy | `coordination_strategy` |
| Sequential Steps | `OrchestrationEngine.execute_task()` |
| Agent Handoff | `team.agents[]` with routing |
| Conditional Branches | Custom routing logic |

## Core Services

### 1. Agent Service
- Creates Agent instances from UI configuration
- Maps UI forms to agenticaiframework primitives
- Manages agent lifecycle (create, update, delete)

### 2. Execution Engine
- Wraps `OrchestrationEngine` for execution
- Records execution logs, tool calls, and errors
- Tracks token usage and cost estimates

### 3. Tool Registry Service
- Manages built-in tools (web search, RAG, file reader, API caller)
- Supports custom tool registration via JSON schema
- Validates tool input/output contracts

### 4. Memory Service
- Configures memory per agent
- Supports session memory (per run) and persistent memory
- Integrates with vector store for knowledge base

### 5. Observability Service
- Captures execution steps
- Records tool calls with inputs/outputs
- Logs errors and retries
- Calculates token usage and cost estimates

## Demo Agents

### 1. Research & Insight Agent
- **Purpose**: Accept topic, search web + documents, produce structured report
- **Tools**: Web Search, RAG, Summarization
- **Tests**: Tool calling, RAG, memory, multi-step reasoning

### 2. Automation / Ops Agent
- **Purpose**: Execute operational tasks with deterministic outputs
- **Tools**: File Reader, Data Analyzer, API Caller
- **Tests**: Tool orchestration, error handling, reliability

### 3. Multi-Agent Orchestrator
- **Purpose**: Demonstrate agent coordination
- **Agents**: Planner → Executor → Critic
- **Flow**: Sequential multi-agent workflow with handoffs

## How to Add New Tools

1. Create a tool class in `backend/tools/`:

```python
from agenticaiframework.tools import BaseTool, register_tool

@register_tool(category="custom", version="1.0")
class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "Description of what this tool does"
    
    # JSON schema for input validation
    input_schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1"]
    }
    
    def execute(self, param1: str, param2: int = 0) -> dict:
        # Tool logic here
        return {"result": "..."}
```

2. Register in tool registry service
3. Tool will automatically appear in Agent Builder UI

## How to Add New Agents

1. Define agent configuration:

```python
AGENT_CONFIG = {
    "name": "MyAgent",
    "role": "Specialist Role",
    "capabilities": ["tool1", "tool2"],
    "config": {
        "model": "gpt-4",
        "temperature": 0.7,
        "system_prompt": "You are..."
    }
}
```

2. Create agent via API or UI
3. Agent will be available for execution

## Running the Platform

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Running Demo Agents
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/agents/demo/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI browser automation competitors"}'
```

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic, SQLite/PostgreSQL
- **Frontend**: Next.js 14+, TypeScript, React, TailwindCSS (if needed)
- **AI Framework**: agenticaiframework
- **Vector Store**: ChromaDB (for RAG)
- **Caching**: Redis (optional)
