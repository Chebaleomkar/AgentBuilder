"""
Multi-Agent Orchestrator using AgenticAI Framework
Wraps Team and WorkflowManager for multi-agent workflows
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import asyncio

from agenticaiframework import Agent, AgentConfig, Team, WorkflowManager, MemoryManager

from app.core.config import settings
from app.models.workflow import WorkflowResponse
from app.models.agent import AgentResponse
from app.models.execution import LogLevel
from app.services.execution_service import ExecutionContext


class AgenticOrchestrator:
    """
    Multi-agent orchestration using agenticaiframework's Team primitive.
    
    Supports workflow strategies:
    - sequential: Agents run one after another
    - supervisor: One agent coordinates others
    - peer: All agents run in parallel
    - conditional: Branch based on output conditions
    """
    
    def __init__(
        self,
        workflow: WorkflowResponse,
        agents: List[AgentResponse],
        context: ExecutionContext
    ):
        self.workflow = workflow
        self.agent_configs = agents
        self.context = context
        self.memory = MemoryManager()
        self._team = None
        self._initialize_team()
    
    def _create_agent(self, agent_config: AgentResponse) -> Agent:
        """Create an agenticaiframework Agent from our config"""
        config = AgentConfig(
            name=agent_config.name,
            role=agent_config.role,
            goal=agent_config.goal or f"Complete tasks as {agent_config.role}",
            model=agent_config.model,
            temperature=agent_config.temperature
        )
        return Agent(config=config, memory=self.memory)
    
    def _get_workflow_manager(self) -> WorkflowManager:
        """Map our strategy to agenticaiframework WorkflowManager"""
        strategy = self.workflow.coordination_strategy
        
        if strategy == "sequential":
            return WorkflowManager.sequential()
        elif strategy == "supervisor":
            return WorkflowManager.supervisor()
        elif strategy == "peer":
            return WorkflowManager.parallel()
        elif strategy == "conditional":
            return WorkflowManager.conditional()
        else:
            # Default to sequential
            return WorkflowManager.sequential()
    
    def _initialize_team(self):
        """Create agenticaiframework Team from workflow configuration"""
        # Create agents from configs
        agents = [self._create_agent(cfg) for cfg in self.agent_configs]
        
        # Get workflow manager
        workflow_manager = self._get_workflow_manager()
        
        # Create the team
        self._team = Team(
            name=self.workflow.name,
            agents=agents,
            workflow=workflow_manager
        )
        
        self.context.log(
            f"Initialized Team: {self.workflow.name} with {len(agents)} agents",
            source="orchestrator",
            metadata={
                "strategy": self.workflow.coordination_strategy,
                "agents": [a.name for a in self.agent_configs]
            }
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the multi-agent workflow.
        
        Uses agenticaiframework's Team.execute() with full observability.
        """
        query = self._extract_query(input_data)
        
        self.context.log(
            f"Starting multi-agent execution",
            source="orchestrator",
            metadata={"strategy": self.workflow.coordination_strategy}
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Execute the team workflow
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._team.execute(query)
            )
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Extract output
            output = result.output if hasattr(result, 'output') else str(result)
            
            # Parse structured output
            try:
                parsed_output = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                parsed_output = {"response": output}
            
            # Log agent steps if available
            if hasattr(result, 'agent_results'):
                for i, agent_result in enumerate(result.agent_results):
                    self.context.start_step(
                        f"Agent: {self.agent_configs[i].name}",
                        "agent"
                    )
                    self.context.complete_step(
                        output={"result": str(agent_result)}
                    )
            
            self.context.log(
                f"Multi-agent execution completed in {duration_ms}ms",
                source="orchestrator"
            )
            
            return {
                "result": parsed_output,
                "raw_response": output,
                "duration_ms": duration_ms,
                "framework": "agenticaiframework",
                "workflow": self.workflow.name,
                "strategy": self.workflow.coordination_strategy,
                "agents_count": len(self.agent_configs),
                "token_usage": self.context.token_usage.model_dump()
            }
            
        except Exception as e:
            self.context.log(
                f"Multi-agent execution failed: {str(e)}",
                level=LogLevel.ERROR,
                source="orchestrator"
            )
            raise
    
    def _extract_query(self, input_data: Dict[str, Any]) -> str:
        """Extract query from input data"""
        if isinstance(input_data, str):
            return input_data
        
        if "task" in input_data:
            return input_data["task"]
        elif "query" in input_data:
            return input_data["query"]
        elif "prompt" in input_data:
            return input_data["prompt"]
        else:
            return json.dumps(input_data)
