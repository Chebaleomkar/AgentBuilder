"""
Demo Agent API Routes
Pre-built demo agents for showcasing platform capabilities
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.agent_service import agent_service
from app.services.workflow_service import workflow_service
from app.services.execution_service import execution_service
from app.models.agent import AgentCreate, MemoryType
from app.models.workflow import WorkflowCreate, WorkflowStep, StepType, CoordinationStrategy
from app.core.config import settings


router = APIRouter(prefix="/demo", tags=["Demo Agents"])


def get_default_model() -> str:
    """
    Get the best available model based on configured API keys.
    Priority: GROQ > Gemini > OpenAI
    """
    # Check GROQ first - it's the most reliable for the user
    if os.getenv("GROQ_API_KEY"):
        return "llama-3.3-70b-versatile"
    elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
        return "gemini-1.5-flash"
    elif settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
        return "gpt-4"
    else:
        # Default to GROQ's Llama model
        return "llama-3.3-70b-versatile"


# ========== Request Models ==========

class ResearchRequest(BaseModel):
    """Request for Research Agent"""
    topic: str
    max_sources: int = 5
    include_summary: bool = True


class AutomationRequest(BaseModel):
    """Request for Automation Agent"""
    data: List[Dict[str, Any]]
    task: str = "analyze"


class MultiAgentRequest(BaseModel):
    """Request for Multi-Agent Orchestrator"""
    task: str
    context: Optional[Dict[str, Any]] = None


# ========== Demo Agent Configurations ==========

RESEARCH_AGENT_CONFIG = AgentCreate(
    name="Research Agent",
    role="Research Specialist",
    goal="Analyze topics and produce comprehensive, structured research reports",
    instructions="""You are a Research & Insight Agent. Your job is to:
1. Accept a topic or research question
2. Search the web for relevant information
3. Analyze and synthesize the findings
4. Produce a structured report with:
   - Executive Summary
   - Key Findings
   - Detailed Analysis
   - Sources
   - Recommendations

Always cite your sources and provide balanced, factual information.
When using web_search, make multiple targeted queries to gather comprehensive data.
Structure your final output in a clear, professional format.""",
    model=get_default_model(),
    temperature=0.7,
    tools=["web_search", "text_summarizer"],
    memory_type=MemoryType.SESSION
)

AUTOMATION_AGENT_CONFIG = AgentCreate(
    name="Automation Agent",
    role="Operations Specialist",
    goal="Execute operational tasks and produce deterministic structured outputs",
    instructions="""You are an Automation / Ops Agent. Your job is to:
1. Accept structured data inputs (CSV, JSON, etc.)
2. Analyze the data for patterns and insights
3. Execute requested operations reliably
4. Return structured, deterministic outputs

Key behaviors:
- Always validate input data before processing
- Handle errors gracefully with clear messages
- Return outputs in consistent JSON format
- Include metadata about the operation performed
- Be precise and deterministic in your analysis

Output format:
{
    "status": "success" | "error",
    "operation": "description of what was done",
    "results": { ... },
    "metadata": {
        "records_processed": number,
        "processing_time": "...",
        "warnings": []
    }
}""",
    model=get_default_model(),
    temperature=0.3,  # Lower for more deterministic outputs
    tools=["data_analyzer", "file_reader"],
    memory_type=MemoryType.SESSION
)

PLANNER_AGENT_CONFIG = AgentCreate(
    name="Planner Agent",
    role="Strategic Planner",
    goal="Break down complex tasks into actionable steps",
    instructions="""You are the Planner Agent in a multi-agent system.
Your job is to:
1. Analyze the incoming task
2. Break it down into clear, actionable steps
3. Identify what information or actions are needed
4. Create a structured execution plan

Output your plan in this format:
{
    "task_analysis": "Brief analysis of the task",
    "steps": [
        {"step": 1, "action": "...", "description": "..."},
        {"step": 2, "action": "...", "description": "..."}
    ],
    "required_information": ["..."],
    "expected_output": "Description of expected final output"
}

Be thorough but concise. Focus on actionable items.""",
    model=get_default_model(),
    temperature=0.5,
    tools=[],
    memory_type=MemoryType.SESSION
)

EXECUTOR_AGENT_CONFIG = AgentCreate(
    name="Executor Agent",
    role="Task Executor",
    goal="Execute planned steps and gather required information",
    instructions="""You are the Executor Agent in a multi-agent system.
Your job is to:
1. Receive a plan from the Planner Agent
2. Execute each step systematically
3. Use available tools to gather information
4. Compile results from each step

Follow the plan precisely. If you encounter issues:
- Document the problem clearly
- Attempt alternative approaches
- Report what was accomplished

Output format:
{
    "steps_completed": [
        {"step": 1, "status": "completed", "result": "..."},
        {"step": 2, "status": "completed", "result": "..."}
    ],
    "gathered_information": { ... },
    "issues_encountered": [],
    "ready_for_review": true
}""",
    model=get_default_model(),
    temperature=0.5,
    tools=["web_search", "api_caller", "data_analyzer"],
    memory_type=MemoryType.SESSION
)

CRITIC_AGENT_CONFIG = AgentCreate(
    name="Critic Agent",
    role="Quality Reviewer",
    goal="Review execution results and provide final polished output",
    instructions="""You are the Critic Agent in a multi-agent system.
Your job is to:
1. Review the execution results from the Executor
2. Evaluate completeness and quality
3. Identify any gaps or issues
4. Produce the final polished output

Evaluation criteria:
- Completeness: Were all steps executed?
- Accuracy: Is the information correct?
- Quality: Is the output well-structured?
- Actionability: Are recommendations clear?

Output format:
{
    "review": {
        "completeness_score": 1-10,
        "quality_score": 1-10,
        "issues_found": []
    },
    "final_output": {
        "summary": "...",
        "key_findings": [...],
        "recommendations": [...],
        "detailed_results": { ... }
    },
    "meta": {
        "agents_involved": ["Planner", "Executor", "Critic"],
        "review_notes": "..."
    }
}""",
    model=get_default_model(),
    temperature=0.5,
    tools=["text_summarizer"],
    memory_type=MemoryType.SESSION
)


# ========== Demo Endpoints ==========

@router.post("/research")
async def run_research_agent(request: ResearchRequest):
    """
    🥇 Research & Insight Agent
    
    Accepts a topic, searches web + documents, produces a structured report.
    
    Tests: Tool calling, RAG, Memory, Multi-step reasoning
    """
    # Create or get the research agent
    existing_agents = await agent_service.search("Research Agent")
    
    if existing_agents:
        agent = existing_agents[0]
    else:
        agent = await agent_service.create(RESEARCH_AGENT_CONFIG)
    
    # Execute the agent
    input_data = {
        "task": f"Research the following topic and produce a comprehensive report: {request.topic}",
        "context": {
            "max_sources": request.max_sources,
            "include_summary": request.include_summary
        }
    }
    
    result = await execution_service.execute_agent(
        agent_id=agent.id,
        input_data=input_data,
        trigger_type="demo"
    )
    
    return result


@router.post("/automation")
async def run_automation_agent(request: AutomationRequest):
    """
    🥈 Automation / Ops Agent
    
    Executes operational tasks with deterministic structured output.
    
    Tests: Tool orchestration, Error handling, Reliability
    """
    # Create or get the automation agent
    existing_agents = await agent_service.search("Automation Agent")
    
    if existing_agents:
        agent = existing_agents[0]
    else:
        agent = await agent_service.create(AUTOMATION_AGENT_CONFIG)
    
    # Execute the agent
    input_data = {
        "task": f"Perform the following operation on the provided data: {request.task}",
        "data": request.data
    }
    
    result = await execution_service.execute_agent(
        agent_id=agent.id,
        input_data=input_data,
        trigger_type="demo"
    )
    
    return result


@router.post("/multi-agent")
async def run_multi_agent_orchestrator(request: MultiAgentRequest):
    """
    🥉 Multi-Agent Orchestrator
    
    Planner → Executor → Critic workflow.
    
    Tests: Agent coordination, Workflow orchestration, Framework leverage
    """
    # Create agents if they don't exist
    planner = None
    executor = None
    critic = None
    
    # Check for existing agents
    planners = await agent_service.search("Planner Agent")
    executors = await agent_service.search("Executor Agent")
    critics = await agent_service.search("Critic Agent")
    
    if planners:
        planner = planners[0]
    else:
        planner = await agent_service.create(PLANNER_AGENT_CONFIG)
    
    if executors:
        executor = executors[0]
    else:
        executor = await agent_service.create(EXECUTOR_AGENT_CONFIG)
    
    if critics:
        critic = critics[0]
    else:
        critic = await agent_service.create(CRITIC_AGENT_CONFIG)
    
    # Create or get the workflow
    existing_workflows = await workflow_service.get_all()
    workflow = None
    
    for wf in existing_workflows.workflows:
        if wf.name == "Multi-Agent Orchestrator Demo":
            workflow = wf
            break
    
    if not workflow:
        workflow = await workflow_service.create(WorkflowCreate(
            name="Multi-Agent Orchestrator Demo",
            description="Planner → Executor → Critic workflow demonstrating multi-agent coordination",
            coordination_strategy=CoordinationStrategy.SEQUENTIAL,
            agents=[planner.id, executor.id, critic.id],
            steps=[
                WorkflowStep(
                    name="Planning Phase",
                    type=StepType.AGENT,
                    agent_id=planner.id
                ),
                WorkflowStep(
                    name="Execution Phase",
                    type=StepType.AGENT,
                    agent_id=executor.id
                ),
                WorkflowStep(
                    name="Review Phase",
                    type=StepType.AGENT,
                    agent_id=critic.id
                )
            ]
        ))
    
    # Import here to avoid circular imports
    from app.engine.orchestrator import MultiAgentOrchestrator
    from app.services.execution_service import ExecutionContext
    
    # Create execution
    execution = await execution_service.create_execution(
        workflow_id=workflow.id,
        input_data={"task": request.task, "context": request.context or {}},
        trigger_type="demo"
    )
    
    context = ExecutionContext(execution.id)
    
    try:
        await execution_service.update_status(
            execution.id,
            execution_service.ExecutionStatus.RUNNING
        )
        
        orchestrator = MultiAgentOrchestrator(workflow, context)
        result = await orchestrator.execute({
            "task": request.task,
            "context": request.context or {}
        })
        
        await execution_service.update_status(
            execution.id,
            execution_service.ExecutionStatus.COMPLETED,
            output_data=result,
            token_usage=context.token_usage
        )
        
        await execution_service.save_context(execution.id, context)
        
        return await execution_service.get_detail(execution.id)
        
    except Exception as e:
        await execution_service.update_status(
            execution.id,
            execution_service.ExecutionStatus.FAILED,
            error_message=str(e)
        )
        await execution_service.save_context(execution.id, context)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_demo_agent_configs():
    """List all demo agent configurations"""
    return {
        "agents": [
            {
                "id": "research",
                "name": RESEARCH_AGENT_CONFIG.name,
                "role": RESEARCH_AGENT_CONFIG.role,
                "goal": RESEARCH_AGENT_CONFIG.goal,
                "tools": RESEARCH_AGENT_CONFIG.tools
            },
            {
                "id": "automation",
                "name": AUTOMATION_AGENT_CONFIG.name,
                "role": AUTOMATION_AGENT_CONFIG.role,
                "goal": AUTOMATION_AGENT_CONFIG.goal,
                "tools": AUTOMATION_AGENT_CONFIG.tools
            },
            {
                "id": "planner",
                "name": PLANNER_AGENT_CONFIG.name,
                "role": PLANNER_AGENT_CONFIG.role,
                "goal": PLANNER_AGENT_CONFIG.goal,
                "tools": PLANNER_AGENT_CONFIG.tools
            },
            {
                "id": "executor",
                "name": EXECUTOR_AGENT_CONFIG.name,
                "role": EXECUTOR_AGENT_CONFIG.role,
                "goal": EXECUTOR_AGENT_CONFIG.goal,
                "tools": EXECUTOR_AGENT_CONFIG.tools
            },
            {
                "id": "critic",
                "name": CRITIC_AGENT_CONFIG.name,
                "role": CRITIC_AGENT_CONFIG.role,
                "goal": CRITIC_AGENT_CONFIG.goal,
                "tools": CRITIC_AGENT_CONFIG.tools
            }
        ]
    }
