"""
Multi-Agent Orchestrator
Handles multi-agent workflows with sequential, parallel, and conditional execution
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

from app.models.workflow import (
    WorkflowResponse, WorkflowStep, StepType, CoordinationStrategy
)
from app.models.agent import AgentResponse
from app.models.execution import LogLevel
from app.services.execution_service import ExecutionContext
from app.services.agent_service import agent_service
from app.engine.executor import AgentExecutor


class OrchestratorContext:
    """Extended context for multi-agent orchestration"""
    
    def __init__(self, execution_context: ExecutionContext):
        self.context = execution_context
        self.shared_memory: Dict[str, Any] = {}
        self.agent_outputs: Dict[str, Any] = {}
        self.current_agent: Optional[str] = None
    
    def set_shared(self, key: str, value: Any):
        """Set a value in shared memory"""
        self.shared_memory[key] = value
    
    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get a value from shared memory"""
        return self.shared_memory.get(key, default)
    
    def record_agent_output(self, agent_id: str, output: Any):
        """Record an agent's output"""
        self.agent_outputs[agent_id] = output


class MultiAgentOrchestrator:
    """
    Orchestrates multi-agent workflows.
    
    Supports:
    - Sequential execution (agents run one after another)
    - Supervisor pattern (one agent coordinates others)
    - Peer pattern (agents collaborate)
    - Conditional branching (different paths based on conditions)
    """
    
    def __init__(self, workflow: WorkflowResponse, context: ExecutionContext):
        self.workflow = workflow
        self.context = context
        self.orch_context = OrchestratorContext(context)
        self.agents_cache: Dict[str, AgentResponse] = {}
    
    async def load_agents(self):
        """Load all agents needed for the workflow"""
        agents = await agent_service.get_by_ids(self.workflow.agents)
        for agent in agents:
            self.agents_cache[agent.id] = agent
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        """
        self.context.log(
            f"Starting workflow: {self.workflow.name}",
            source="orchestrator"
        )
        
        # Load agents
        await self.load_agents()
        
        # Store initial input in shared memory
        self.orch_context.set_shared("input", input_data)
        self.orch_context.set_shared("original_input", input_data)
        
        strategy = self.workflow.coordination_strategy
        
        if strategy == CoordinationStrategy.SEQUENTIAL:
            result = await self._execute_sequential(input_data)
        elif strategy == CoordinationStrategy.SUPERVISOR:
            result = await self._execute_supervisor(input_data)
        elif strategy == CoordinationStrategy.PEER:
            result = await self._execute_peer(input_data)
        elif strategy == CoordinationStrategy.CONDITIONAL:
            result = await self._execute_conditional(input_data)
        else:
            raise ValueError(f"Unknown coordination strategy: {strategy}")
        
        self.context.log(
            f"Workflow completed: {self.workflow.name}",
            source="orchestrator"
        )
        
        return {
            "workflow_id": self.workflow.id,
            "workflow_name": self.workflow.name,
            "result": result,
            "agent_outputs": self.orch_context.agent_outputs,
            "shared_memory": self.orch_context.shared_memory
        }
    
    async def _execute_sequential(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents sequentially, passing output to next agent"""
        self.context.log(
            f"Executing sequential workflow with {len(self.workflow.agents)} agents",
            source="orchestrator"
        )
        
        current_input = input_data
        final_result = None
        
        for i, agent_id in enumerate(self.workflow.agents):
            agent = self.agents_cache.get(agent_id)
            if not agent:
                self.context.log(
                    f"Agent not found: {agent_id}",
                    level=LogLevel.WARNING,
                    source="orchestrator"
                )
                continue
            
            self.context.log(
                f"Executing agent {i+1}/{len(self.workflow.agents)}: {agent.name}",
                source="orchestrator"
            )
            
            # Start step for this agent
            self.context.start_step(f"Agent: {agent.name}", "agent", agent_id)
            self.context.current_step.input_data = current_input
            
            try:
                # Execute agent
                executor = AgentExecutor(agent, self.context)
                result = await executor.execute(current_input)
                
                # Record output
                self.orch_context.record_agent_output(agent_id, result)
                
                # Use result as input for next agent
                if "result" in result:
                    current_input = {
                        "previous_agent": agent.name,
                        "previous_output": result["result"],
                        "context": self.orch_context.shared_memory
                    }
                
                final_result = result
                self.context.complete_step(output=result)
                
            except Exception as e:
                self.context.complete_step(error=str(e))
                raise
        
        return final_result
    
    async def _execute_supervisor(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Supervisor pattern: First agent coordinates others.
        The supervisor decides which agent(s) to call.
        """
        if not self.workflow.agents:
            return {"error": "No agents in workflow"}
        
        supervisor_id = self.workflow.agents[0]
        supervisor = self.agents_cache.get(supervisor_id)
        
        if not supervisor:
            return {"error": f"Supervisor agent not found: {supervisor_id}"}
        
        self.context.log(
            f"Supervisor agent: {supervisor.name}",
            source="orchestrator"
        )
        
        # Get list of available worker agents
        worker_agents = []
        for agent_id in self.workflow.agents[1:]:
            agent = self.agents_cache.get(agent_id)
            if agent:
                worker_agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "goal": agent.goal
                })
        
        # Enhance supervisor input with worker info
        supervisor_input = {
            **input_data,
            "available_workers": worker_agents,
            "instruction": "You are the supervisor. Analyze the task and delegate to appropriate workers."
        }
        
        # Execute supervisor
        self.context.start_step(f"Supervisor: {supervisor.name}", "agent", supervisor_id)
        executor = AgentExecutor(supervisor, self.context)
        result = await executor.execute(supervisor_input)
        self.context.complete_step(output=result)
        
        return result
    
    async def _execute_peer(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Peer pattern: All agents work on the same input in parallel,
        then results are aggregated.
        """
        self.context.log(
            f"Executing peer workflow with {len(self.workflow.agents)} agents in parallel",
            source="orchestrator"
        )
        
        # Execute all agents in parallel
        tasks = []
        for agent_id in self.workflow.agents:
            agent = self.agents_cache.get(agent_id)
            if agent:
                tasks.append(self._execute_single_agent(agent, input_data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        aggregated = {
            "agents": [],
            "errors": []
        }
        
        for i, result in enumerate(results):
            agent_id = self.workflow.agents[i]
            agent = self.agents_cache.get(agent_id)
            
            if isinstance(result, Exception):
                aggregated["errors"].append({
                    "agent_id": agent_id,
                    "agent_name": agent.name if agent else "Unknown",
                    "error": str(result)
                })
            else:
                aggregated["agents"].append({
                    "agent_id": agent_id,
                    "agent_name": agent.name if agent else "Unknown",
                    "result": result
                })
        
        return aggregated
    
    async def _execute_conditional(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conditional execution based on workflow steps.
        """
        if not self.workflow.steps:
            # Fall back to sequential if no steps defined
            return await self._execute_sequential(input_data)
        
        self.context.log(
            f"Executing conditional workflow with {len(self.workflow.steps)} steps",
            source="orchestrator"
        )
        
        current_input = input_data
        executed_steps = []
        
        # Start from first step
        current_step = self.workflow.steps[0] if self.workflow.steps else None
        
        while current_step:
            step_result = await self._execute_step(current_step, current_input)
            executed_steps.append({
                "step_id": current_step.id,
                "step_name": current_step.name,
                "result": step_result
            })
            
            # Determine next step
            next_step_id = None
            if step_result.get("success", True):
                next_step_id = current_step.on_success
            else:
                next_step_id = current_step.on_failure
            
            if not next_step_id and current_step.next_steps:
                next_step_id = current_step.next_steps[0]
            
            # Find next step
            current_step = None
            if next_step_id:
                for step in self.workflow.steps:
                    if step.id == next_step_id:
                        current_step = step
                        break
            
            # Update input for next step
            if step_result.get("output"):
                current_input = {
                    "previous_step": executed_steps[-1]["step_name"],
                    "previous_output": step_result["output"],
                    "context": self.orch_context.shared_memory
                }
        
        return {
            "executed_steps": executed_steps,
            "final_output": executed_steps[-1]["result"] if executed_steps else None
        }
    
    async def _execute_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        self.context.log(
            f"Executing step: {step.name} (type: {step.type})",
            source="orchestrator"
        )
        
        if step.type == StepType.AGENT:
            if not step.agent_id:
                return {"error": "No agent_id specified for agent step"}
            
            agent = self.agents_cache.get(step.agent_id)
            if not agent:
                return {"error": f"Agent not found: {step.agent_id}"}
            
            return await self._execute_single_agent(agent, input_data)
        
        elif step.type == StepType.CONDITION:
            # Evaluate condition
            condition = step.condition or "true"
            try:
                # Simple condition evaluation (be careful with security!)
                result = eval(condition, {"input": input_data, "context": self.orch_context.shared_memory})
                return {"success": bool(result), "condition": condition}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif step.type == StepType.HANDOFF:
            # Similar to agent, but with handoff semantics
            if not step.agent_id:
                return {"error": "No agent_id specified for handoff step"}
            
            agent = self.agents_cache.get(step.agent_id)
            if not agent:
                return {"error": f"Agent not found: {step.agent_id}"}
            
            # Add handoff context
            handoff_input = {
                **input_data,
                "handoff": True,
                "handoff_from": step.name
            }
            
            return await self._execute_single_agent(agent, handoff_input)
        
        else:
            return {"error": f"Unknown step type: {step.type}"}
    
    async def _execute_single_agent(
        self,
        agent: AgentResponse,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single agent"""
        self.context.start_step(f"Agent: {agent.name}", "agent", agent.id)
        self.context.current_step.input_data = input_data
        
        try:
            executor = AgentExecutor(agent, self.context)
            result = await executor.execute(input_data)
            
            self.orch_context.record_agent_output(agent.id, result)
            self.context.complete_step(output=result)
            
            return {"success": True, "output": result}
            
        except Exception as e:
            self.context.complete_step(error=str(e))
            return {"success": False, "error": str(e)}
