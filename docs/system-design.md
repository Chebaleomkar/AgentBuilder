# System Design

This document explains the high-level architecture and design decisions behind AgentBuilder.

## 🎨 Design Philosophy

### 1. UI-First, Not Code-First

Traditional agent frameworks require writing Python or JavaScript. We flip this—you configure agents through forms, and the system generates the execution logic.

```
Traditional:  Write Code → Deploy → Test → Iterate
AgentBuilder: Fill Form → Run → Observe → Adjust
```

### 2. Observability is Not Optional

Every execution captures:
- Each step the agent takes
- Every tool call with inputs/outputs
- Token usage and cost estimates
- Timing for performance analysis

You should never wonder *"what did my agent do?"*

### 3. Multi-Provider Support

We don't lock you into one LLM provider. The same agent definition works with:
- OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5)
- Google Gemini (1.5 Pro, 1.5 Flash, 2.0)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Agents  │  │Workflows │  │Playground│  │      Logs        │ │
│  │  Builder │  │ Designer │  │ Executor │  │ (Observability)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼─────────────────┼───────────┘
        │             │             │                 │
        ▼             ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     REST API (FastAPI)                          │
│  /api/v1/agents  /api/v1/workflows  /api/v1/executions         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐
│   Services   │    │    Engine    │    │      Database        │
│  (CRUD Ops)  │    │  (Executor)  │    │     (MongoDB)        │
└──────────────┘    └───────┬──────┘    └──────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  OpenAI  │  │  Gemini  │  │   Tools  │
        │   API    │  │   API    │  │ Registry │
        └──────────┘  └──────────┘  └──────────┘
```

---

## 📦 Core Components

### 1. Agent Configuration Store

Agents are stored as JSON documents in MongoDB:

```json
{
  "id": "agent_abc123",
  "name": "Research Agent",
  "role": "Research Specialist",
  "goal": "Find and synthesize information",
  "instructions": "Search the web, analyze results...",
  "model": "gpt-4",
  "temperature": 0.7,
  "tools": ["web_search", "text_summarizer"],
  "memory_type": "session",
  "status": "active"
}
```

No code is stored—just configuration. The execution engine interprets this at runtime.

### 2. Execution Engine

The engine is the brain of AgentBuilder. It:

1. **Loads agent config** from the database
2. **Builds system prompt** from role, goal, and instructions
3. **Registers tools** based on the agent's tool list
4. **Calls the LLM** with the user's input
5. **Handles tool calls** by executing registered functions
6. **Loops** until the agent produces a final response
7. **Records everything** to the execution log

```python
# Simplified execution flow
async def execute(agent, input):
    messages = build_messages(agent, input)
    
    while not done:
        response = await call_llm(messages)
        
        if response.has_tool_calls:
            results = await execute_tools(response.tool_calls)
            messages.append(results)
        else:
            return response.content
```

### 3. Multi-Agent Orchestrator

For workflows with multiple agents, the orchestrator supports:

| Strategy | Behavior |
|----------|----------|
| **Sequential** | Agent A → Agent B → Agent C |
| **Supervisor** | One agent decides which others to call |
| **Peer** | All agents run in parallel, results merged |
| **Conditional** | Branch to different agents based on conditions |

### 4. Tool Registry

Tools are registered with:
- **Name** - How the agent references it
- **Description** - What the LLM sees
- **Input Schema** - JSON Schema for parameters
- **Handler** - The actual Python function

```python
# Example tool registration
tools = {
    "web_search": {
        "description": "Search the web for information",
        "parameters": {
            "query": {"type": "string", "description": "Search query"}
        },
        "handler": async_web_search_function
    }
}
```

---

## 🔐 Security Considerations

1. **API Keys** - Stored in env vars, never in database
2. **Tool Sandboxing** - Tools run with limited permissions
3. **Input Validation** - Pydantic validates all API inputs
4. **CORS** - Configured for specific origins only

---

## 📈 Scalability Path

Current architecture supports:
- **Hundreds of agents** - MongoDB handles document scale
- **Concurrent executions** - Async Python + background tasks
- **Multiple LLM providers** - Abstracted behind executor interface

Future scaling would involve:
- Redis for execution queuing
- Kubernetes for horizontal scaling
- Dedicated vector DB for RAG at scale

---

## 🎯 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| MongoDB over SQL | Flexible schema for agent configs |
| FastAPI over Flask | Native async, automatic OpenAPI docs |
| Next.js App Router | Server components, better DX |
| Zustand over Redux | Simpler state management |
| Provider abstraction | Easy to add new LLM providers |

---

*Next: [Tech Stack →](./tech-stack.md)*
