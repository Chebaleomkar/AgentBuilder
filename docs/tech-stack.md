# Tech Stack

A breakdown of every technology used in AgentBuilder and why we chose it.

---

## 🐍 Backend

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Primary language |
| **FastAPI** | 0.109 | Web framework |
| **Uvicorn** | 0.27 | ASGI server |
| **Pydantic** | 2.5 | Data validation |

**Why FastAPI?**
- Native async/await support (critical for LLM calls)
- Automatic OpenAPI documentation
- Type hints → runtime validation
- Best-in-class performance for Python

### Database

| Technology | Purpose |
|------------|---------|
| **MongoDB** | Primary data store |
| **Motor** | Async MongoDB driver |

**Why MongoDB?**
- Agent configs are document-shaped (JSON-like)
- Schema flexibility as features evolve
- Easy to query nested tool configurations

### AI/ML

| Technology | Version | Purpose |
|------------|---------|---------|
| **OpenAI SDK** | 1.12 | GPT models |
| **google-generativeai** | 0.8 | Gemini models |
| **Anthropic** | 0.18 | Claude (planned) |
| **Tiktoken** | 0.5 | Token counting |

### Vector Store (RAG)

| Technology | Purpose |
|------------|---------|
| **ChromaDB** | Local vector database |

Used for knowledge-base memory and RAG search tools.

### Utilities

| Technology | Purpose |
|------------|---------|
| **Tenacity** | Retry logic for API calls |
| **httpx** | Async HTTP client |
| **python-dotenv** | Environment management |
| **structlog** | Structured logging |

---

## ⚛️ Frontend

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.2 | React framework |
| **React** | 18.2 | UI library |
| **TypeScript** | 5.3 | Type safety |

**Why Next.js 14?**
- App Router for better layouts
- Server Components for performance
- Built-in API routes if needed
- Great DX with hot reload

### Styling

| Technology | Purpose |
|------------|---------|
| **Tailwind CSS** | Utility-first CSS |
| **clsx** | Conditional classes |
| **tailwind-merge** | Merge Tailwind classes |

**Design System:**
- Dark theme by default
- Glassmorphism effects
- Gradient accents (primary → accent)
- Custom animations

### State Management

| Technology | Purpose |
|------------|---------|
| **TanStack Query** | Server state (API data) |
| **Zustand** | Client state (UI state) |

**Why this combo?**
- TanStack Query handles caching, refetching, loading states
- Zustand is tiny (~1kb) for simple UI state
- No prop drilling, no Redux boilerplate

### UI Components

| Technology | Purpose |
|------------|---------|
| **Lucide React** | Icons |
| **Framer Motion** | Animations |
| **react-hot-toast** | Notifications |
| **react-syntax-highlighter** | Code display |
| **date-fns** | Date formatting |

---

## 🗄️ Data Storage

```
┌─────────────────────────────────────────────┐
│                   MongoDB                   │
├─────────────────────────────────────────────┤
│  Collections:                               │
│  ├── agents      → Agent configurations     │
│  ├── workflows   → Workflow definitions     │
│  ├── executions  → Execution records        │
│  ├── steps       → Execution steps          │
│  ├── logs        → Execution logs           │
│  ├── tools       → Custom tool definitions  │
│  └── users       → User accounts (future)   │
└─────────────────────────────────────────────┘
```

---

## 🔌 External APIs

| API | Purpose | Auth Method |
|-----|---------|-------------|
| OpenAI | GPT models | API Key |
| Google AI | Gemini models | API Key |
| DuckDuckGo | Web search tool | None (public) |

---

## 📁 Project Structure

```
AgentBuilder/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, DB connection
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── engine/        # Execution engine
│   ├── demo_agents/       # Demo API endpoints
│   ├── main.py           # FastAPI app
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # API client, store
│   ├── package.json
│   └── tailwind.config.js
│
└── docs/                 # Documentation
```

---

## 🛠️ Development Tools

| Tool | Purpose |
|------|---------|
| **Git** | Version control |
| **ESLint** | JavaScript linting |
| **Prettier** | Code formatting |
| **pytest** | Python testing |

---

## 📊 Version Compatibility

```
Python:     >= 3.11
Node.js:    >= 18.0
MongoDB:    >= 6.0
npm:        >= 9.0
```

---

*Next: [Application Flow →](./app-flow.md)*
