# Development Guide

Everything you need to start contributing to AgentBuilder.

---

## 🚀 Quick Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Git

### 1. Clone & Setup Backend

```bash
# Clone the repo
git clone https://github.com/Chebaleomkar/AgentBuilder.git
cd AgentBuilder

# Setup Python environment
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Setup Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
```

### 3. Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Codebase Map

### Backend Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── agents.py     # /agents endpoints
│   │   ├── workflows.py  # /workflows endpoints
│   │   ├── tools.py      # /tools endpoints
│   │   └── logs.py       # /executions endpoints
│   │
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings from env vars
│   │   └── database.py   # MongoDB connection
│   │
│   ├── models/           # Pydantic schemas
│   │   ├── agent.py      # Agent request/response models
│   │   ├── workflow.py   # Workflow models
│   │   ├── execution.py  # Execution tracking models
│   │   └── tool.py       # Tool definitions
│   │
│   ├── services/         # Business logic layer
│   │   ├── agent_service.py
│   │   ├── workflow_service.py
│   │   ├── tool_service.py
│   │   └── execution_service.py
│   │
│   └── engine/           # Execution engine
│       ├── executor.py   # LLM calling logic
│       ├── tools.py      # Built-in tool handlers
│       └── orchestrator.py  # Multi-agent coordination
│
├── demo_agents/          # Demo agent endpoints
├── main.py               # FastAPI application
└── requirements.txt      # Python dependencies
```

### Frontend Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── page.tsx      # Homepage
│   │   ├── layout.tsx    # Root layout
│   │   ├── globals.css   # Global styles
│   │   ├── agents/       # Agent pages
│   │   ├── workflows/    # Workflow pages
│   │   ├── playground/   # Execution playground
│   │   └── logs/         # Logs viewer
│   │
│   ├── components/       # Reusable components
│   │   ├── layout/       # Layout components
│   │   └── providers.tsx # React Query provider
│   │
│   └── lib/              # Utilities
│       ├── api.ts        # API client
│       └── store.ts      # Zustand store
│
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

---

## 🔧 Common Tasks

### Adding a New API Endpoint

1. **Create route handler** in `app/api/`:
```python
# app/api/my_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-feature", tags=["My Feature"])

@router.get("")
async def list_items():
    return {"items": []}
```

2. **Register in main.py:**
```python
from app.api import my_feature
app.include_router(my_feature.router, prefix=settings.API_V1_PREFIX)
```

### Adding a New Tool

1. **Add tool definition** in `app/engine/tools.py`:
```python
BUILTIN_TOOLS["my_tool"] = ToolResponse(
    name="my_tool",
    description="What it does",
    category=ToolCategory.CUSTOM,
    input_schema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "..."}
        }
    }
)

async def my_tool_handler(param: str) -> Dict[str, Any]:
    # Tool implementation
    return {"result": "..."}

# Register in get_tool_handlers()
```

### Adding a New LLM Provider

1. **Create executor class** in `app/engine/executor.py`:
```python
class NewProviderExecutor:
    async def call(self, model, messages, temperature, tools):
        # Call the API
        return {
            "content": "...",
            "tool_calls": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
```

2. **Update provider detection:**
```python
def get_provider_for_model(model: str) -> LLMProvider:
    if model.startswith("new-"):
        return LLMProvider.NEW_PROVIDER
    ...
```

### Adding a Frontend Page

1. **Create page file** in `src/app/my-page/page.tsx`:
```tsx
export default function MyPage() {
  return (
    <div className="min-h-screen pt-16">
      <Navbar />
      <div className="container mx-auto px-6 py-8">
        <h1>My Page</h1>
      </div>
    </div>
  );
}
```

2. **Add navigation** in `Navbar.tsx` if needed.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Running Specific Tests

```bash
pytest tests/test_agents.py -v
pytest tests/test_executor.py::test_tool_calls -v
```

---

## 🎨 Code Style

### Python

- Use type hints everywhere
- Async functions for I/O operations
- Pydantic models for validation
- docstrings for public functions

```python
async def create_agent(agent: AgentCreate) -> AgentResponse:
    """Create a new agent in the database.
    
    Args:
        agent: Agent creation data
        
    Returns:
        Created agent with generated ID
    """
    ...
```

### TypeScript

- Use TypeScript strict mode
- Prefer `const` over `let`
- Destructure props
- Use proper types (avoid `any`)

```typescript
interface Props {
  agent: Agent;
  onSave: (agent: Agent) => void;
}

export function AgentCard({ agent, onSave }: Props) {
  ...
}
```

---

## 🐛 Debugging Tips

### Backend

1. **Check logs:**
```python
import structlog
logger = structlog.get_logger()
logger.info("debug_info", data=some_data)
```

2. **Use FastAPI debug mode:**
```bash
# Already enabled with --reload
uvicorn main:app --reload
```

3. **API docs for testing:**
   Open http://localhost:8000/docs

### Frontend

1. **React Query DevTools** (install separately)
2. **Browser DevTools** → Network tab
3. **Console logging:**
```typescript
console.log('Debug:', { variable });
```

---

## 🔐 Environment Variables

### Backend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| MONGO_URI | Yes | MongoDB connection string |
| OPENAI_API_KEY | Yes* | For OpenAI models |
| GEMINI_API_KEY | Yes* | For Gemini models |
| DEBUG | No | Enable debug mode |

*At least one LLM key required.

### Frontend (.env.local)

| Variable | Required | Description |
|----------|----------|-------------|
| NEXT_PUBLIC_API_URL | Yes | Backend API URL |

---

## 📚 Useful Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [TanStack Query](https://tanstack.com/query)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [Google AI](https://ai.google.dev/docs)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Run tests (`pytest` / `npm test`)
5. Commit (`git commit -m 'feat: add amazing feature'`)
6. Push (`git push origin feature/amazing`)
7. Open a Pull Request

---

*Happy coding! 🎉*
