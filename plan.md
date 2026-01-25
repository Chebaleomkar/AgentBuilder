AgentBuilder – Coding Task
UI-first Agent Platform built on agenticaiframework

Task Overview
You are required to design and implement AgentBuilder, a UI-first AI agent platform built on top of the open-source https://github.com/isathish/agenticaiframework 

👉 Strongly encouraged:
Use vibe coding — leverage AI coding tools such as Cursor, Claude, GitHub Copilot, or similar to generate most of the code.
Your responsibility is to review, refine, test, and ensure correctness of the generated code.
👉 Early submission is encouraged.
We value working systems and clarity of thinking over completeness or polish.
👉 Important:
The goal is not to rebuild LLM logic, but to demonstrate how you design systems that allow users to create, run, and observe AI agents in production-like conditions.

AgentBuilder Capabilities 
🧩 Platform Orchestration Layer
AgentBuilder must:
Abstract agenticaiframework primitives behind a clean UI
Convert UI configurations → executable agent definitions
Support:
Single-agent workflows
Multi-agent workflows
Sequential & conditional execution
Agent → Agent handoff
Provide deep observability into execution (logs, tool calls, failures)

🧩 Core Platform Features (Must-Have)
1. Agent Builder (UI)
Users must be able to create agents via simple forms:
Role (who the agent is)
Goal (what it should do)
Instructions / behavior
Tools (select from registry)
Memory settings
All configuration must map directly to agenticaiframework constructs.
⚠️ Drag-and-drop is not required. Simple forms are sufficient.

2. Workflow / Orchestration
Support:
Single-agent execution
Multi-agent workflows
Sequential steps
Conditional branching
Agent → Agent delegation
Example:
Planner Agent → Executor Agent → Critic Agent


3. Tool Registry
Provide a centralized registry:
Prebuilt tools
Web search
RAG (vector DB)
File reader
API caller
Custom tools
User-defined via JSON schema
Input/output contracts
UI-configurable parameters

4. Memory Management
Support:
Session memory (per run)
Persistent memory (per agent / per user)
Vector-store-backed knowledge base
Memory must be configurable per agent.

5. Execution & Logs (Very Important)
Users must be able to:
Run agents manually
View:
Execution steps
Tool calls
Errors & retries
Token usage (basic)
Cost estimates (basic)
Optional:
Thought steps (masked or summarized)
UX must clearly separate:
Define → Run → Observe


🧩 Platform / SaaS Features
6. Multi-Tenant User Management
Support hierarchy:
User → Project → Agents

Role-based access:
Admin
User

7. Agent Marketplace (Phase 2 – Optional)
Prebuilt agent templates
Clone & customize agents
Share within workspace

8. Deployment Modes
Agents must be runnable as:
On-demand
Scheduled
API-triggered (webhooks)

🧩 Top 3 Demo Agents (Must Build)
These agents must be implemented to demonstrate platform capability.

🥇 1. Research & Insight Agent
Accepts a topic or question
Searches web + internal documents
Produces a structured report
Tests:
Tool calling
RAG
Memory
Multi-step reasoning
Example:
“Analyze competitors in AI browser automation and summarize key differences.”

🥈 2. Automation / Ops Agent
Executes operational tasks
Produces deterministic structured output
Tests:
Tool orchestration
Error handling
Reliability
Example:
Upload CSV → Agent returns insights + next actions

🥉 3. Multi-Agent Orchestrator
Agents:
Planner Agent
Executor Agent
Critic Agent
Flow:
Planner → Executor → Critic → Final Output

Tests:
Agent coordination
Workflow orchestration
Framework leverage

🧠 Agent Personality (System Prompt Template)
You are AgentBuilder Core.
You think in agents and workflows
You separate configuration from execution
You value observability and debuggability
You execute deterministically when possible
You coordinate agents when required
You always return structured outputs

✅ Expected Deliverables
1. Backend
Python + FastAPI
agenticaiframework wrapped as a service
APIs:
Create agent
Run agent
Fetch execution logs
Execution engine
Tool registry
Memory service

2. Frontend
Next.js
Agent builder UI
Agent execution playground
Logs & observability panel

3. Demo Agents
Research Agent
Automation Agent
Multi-Agent Orchestrator

4. Documentation
README.md including:
Architecture overview
UI → agenticaiframework mapping
How to add tools
How to add agents
How to run demos

🧪 Evaluation Criteria
Area
What We Look For
Architecture
Clean UI / execution separation
Agent Understanding
Correct framework usage
UX Thinking
Simple, usable UI
Observability
Logs, retries, failures
Extensibility
Easy to add agents/tools
Code Quality
Readable, modular


📦 Method of Submission
Submission Checklist
GitHub repo (AgentBuilder)
Demo video (2–5 mins)
Agent creation
Execution
Logs
Multi-agent workflow
Latest resume
📧 Send to
santosh.thota@analytos.ai
CC: sasidhar.sunkesula@analytos.ai
Subject:
AgentBuilder Platform Task – <Your Name>

🔥 Final Note to Candidates
Use vibe coding aggressively.
Generate fast, validate carefully, and submit early.
We value clarity, working flows, and reasoning more than perfect polish.

