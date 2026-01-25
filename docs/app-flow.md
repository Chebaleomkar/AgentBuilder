# Application Flow

This document walks through how data flows through AgentBuilder for common operations.

---

## 🤖 Creating an Agent

```
User fills form → API validates → MongoDB stores → UI updates
```

### Step-by-Step

1. **User Interface**
   ```
   User fills: Name, Role, Goal, Instructions, Model, Tools
   ```

2. **Frontend sends POST request**
   ```typescript
   await api.post('/agents', {
     name: "Research Agent",
     role: "Research Specialist", 
     model: "gpt-4",
     tools: ["web_search", "text_summarizer"]
   });
   ```

3. **Backend validates with Pydantic**
   ```python
   class AgentCreate(BaseModel):
       name: str
       role: str
       model: str = "gpt-4"
       tools: List[str] = []
   ```

4. **Service layer creates the agent**
   ```python
   async def create(self, agent: AgentCreate):
       doc = agent.model_dump()
       doc["id"] = generate_id()
       doc["created_at"] = datetime.utcnow()
       await db.agents.insert_one(doc)
       return AgentResponse(**doc)
   ```

5. **Frontend receives response, updates UI**
   - TanStack Query invalidates cache
   - User redirected to agent detail page

---

## ▶️ Executing an Agent

This is the core flow—where the magic happens.

```
Input → Build Prompt → Call LLM → Handle Tools → Return Result
         ↑                              │
         └──────── Loop ────────────────┘
```

### Detailed Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  1. USER INPUT                                                   │
│     "Research AI browser automation competitors"                 │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. BUILD MESSAGES                                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ System: You are Research Agent, a Research Specialist.     │  │
│  │         Your goal is to find and synthesize information... │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ User: Research AI browser automation competitors           │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. CALL LLM (OpenAI or Gemini)                                  │
│                                                                  │
│  Request:                                                        │
│  - messages: [system, user]                                      │
│  - tools: [web_search, text_summarizer]                          │
│  - model: gpt-4                                                  │
│  - temperature: 0.7                                              │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. LLM RESPONSE (with tool call)                                │
│                                                                  │
│  "I'll search for AI browser automation tools..."                │
│  Tool Call: web_search(query="AI browser automation tools 2024") │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. EXECUTE TOOL                                                 │
│                                                                  │
│  web_search("AI browser automation tools 2024")                  │
│  → Returns: [{title, url, snippet}, ...]                         │
│                                                                  │
│  ✓ Logged: tool_name, input, output, duration                    │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  6. APPEND TOOL RESULT TO MESSAGES                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ System: ...                                                 │  │
│  │ User: Research AI browser automation...                     │  │
│  │ Assistant: [tool_call: web_search]                          │  │
│  │ Tool: [{title: "Playwright", ...}, ...]                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  7. CALL LLM AGAIN                                               │
│                                                                  │
│  LLM sees tool results, may call more tools or respond.          │
│  Loop continues until no more tool calls.                        │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  8. FINAL RESPONSE                                               │
│                                                                  │
│  "Based on my research, here are the top AI browser automation   │
│   tools: 1. Playwright... 2. Selenium... 3. Puppeteer..."        │
│                                                                  │
│  ✓ Saved to executions collection                                │
│  ✓ Token usage calculated                                        │
│  ✓ Cost estimated                                                │
└──────────────────────────────────────────────────────────────────┘
```

### Code Path

```
main.py
  └── api/agents.py::execute_agent()
        └── services/execution_service.py::execute_agent()
              └── engine/executor.py::AgentExecutor.execute()
                    ├── _build_messages()
                    ├── _call_llm() 
                    │     └── OpenAI or Gemini API
                    ├── _handle_tool_calls()
                    │     └── engine/tools.py handlers
                    └── Return result
```

---

## 🔄 Multi-Agent Workflow

When agents work together:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Planner   │ ──▶ │  Executor   │ ──▶ │   Critic    │
│   Agent     │     │   Agent     │     │   Agent     │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
  "Break down        "Execute each       "Review and
   the task"          step"               polish"
```

### Orchestrator Flow

1. **Load workflow config** (agent IDs, strategy)
2. **Load all agents** from database
3. **Execute based on strategy:**
   - Sequential: Run one after another
   - Peer: Run all in parallel
   - Supervisor: First agent decides order
4. **Pass outputs between agents**
5. **Aggregate final result**

---

## 📊 Observability Flow

Everything is logged automatically:

```
Execution Start
  │
  ├── Step: Build prompt
  │     └── Log: "Starting agent execution"
  │
  ├── Step: LLM Call #1
  │     ├── Log: "Calling GPT-4"
  │     └── Token usage updated
  │
  ├── Step: Tool: web_search
  │     ├── Log: "Executing web_search"
  │     ├── Input: {"query": "..."}
  │     ├── Output: [...]
  │     └── Duration: 234ms
  │
  ├── Step: LLM Call #2
  │     └── ...
  │
  └── Execution Complete
        ├── Total duration
        ├── Total tokens
        └── Cost estimate
```

### Data Stored

```json
{
  "execution_id": "exec_123",
  "agent_id": "agent_abc",
  "status": "completed",
  "input_data": {"query": "..."},
  "output_data": {"response": "..."},
  "steps": [
    {
      "step_name": "Tool: web_search",
      "status": "completed",
      "duration_ms": 234,
      "tool_calls": [...]
    }
  ],
  "logs": [
    {"level": "info", "message": "...", "timestamp": "..."}
  ],
  "token_usage": {
    "input_tokens": 450,
    "output_tokens": 380,
    "total_tokens": 830
  }
}
```

---

## 🔐 Request Lifecycle

Every API request flows through:

```
Request → CORS Check → Route Handler → Service → Database → Response
            │              │              │
            │              │              └── Pydantic validation
            │              └── Dependency injection
            └── Origin validation
```

---

## 🎯 Key Insights

1. **Stateless Execution** - Each execution is independent. No persistent agent "memory" unless configured.

2. **Tool Isolation** - Tools run in the same process but are async. Future: sandboxing.

3. **Fail-Safe Loops** - Max 10 iterations prevents runaway tool loops.

4. **Provider Abstraction** - Switching from GPT-4 to Gemini requires only changing the model field.

---

*Next: [API Reference →](./api-reference.md)*
