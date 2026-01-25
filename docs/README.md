# AgentBuilder Documentation

Welcome to the AgentBuilder documentation. This guide will help you understand the system architecture, design decisions, and how to work with the codebase.

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [System Design](./system-design.md) | High-level architecture and design principles |
| [Tech Stack](./tech-stack.md) | Technologies and frameworks used |
| [Application Flow](./app-flow.md) | How data flows through the system |
| [API Reference](./api-reference.md) | Complete API documentation |
| [Development Guide](./development-guide.md) | Getting started with development |

## 🎯 What is AgentBuilder?

AgentBuilder is a **UI-first AI Agent Platform** that lets you build, run, and observe AI agents without writing code. Think of it as a control panel for your AI automation.

### The Problem We Solve

Building AI agents typically requires:
- Writing boilerplate code for LLM integrations
- Managing tool registries and execution
- Building observability from scratch
- Coordinating multiple agents manually

AgentBuilder handles all of this through a simple web interface.

### Core Concepts

**Agent** - An AI entity with a role, goal, and set of tools it can use.

**Workflow** - A pipeline that connects multiple agents together.

**Execution** - A single run of an agent or workflow, with full logging.

**Tool** - A capability an agent can use (web search, file reading, API calls).

## 🏃 Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000
Frontend: http://localhost:3000
API Docs: http://localhost:8000/docs

---

*Built with ❤️ on top of agenticaiframework*
