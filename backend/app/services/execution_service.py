"""
Execution Service
Core execution engine that wraps agenticaiframework for running agents
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import asyncio
import time
import uuid

from app.core.database import (
    executions_collection, execution_steps_collection, execution_logs_collection
)
from app.core.config import settings
from app.models.execution import (
    ExecutionRequest, ExecutionResponse, ExecutionDetailResponse,
    ExecutionListResponse, ExecutionStep, ExecutionLog, ToolCall,
    ExecutionStatus, StepStatus, LogLevel, TokenUsage,
    execution_to_doc, doc_to_execution, execution_step_to_doc,
    doc_to_execution_step, execution_log_to_doc, doc_to_execution_log
)
from app.models.agent import AgentResponse, to_framework_config
from app.services.agent_service import agent_service


class ExecutionContext:
    """Context for tracking execution state"""
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.steps: List[ExecutionStep] = []
        self.logs: List[ExecutionLog] = []
        self.tool_calls: List[ToolCall] = []
        self.current_step: Optional[ExecutionStep] = None
        self.sequence_number = 0
        self.token_usage = TokenUsage()
    
    def start_step(self, name: str, step_type: str, agent_id: Optional[str] = None) -> ExecutionStep:
        """Start a new execution step"""
        self.sequence_number += 1
        step = ExecutionStep(
            id=str(uuid.uuid4()),
            step_name=name,
            step_type=step_type,
            agent_id=agent_id,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow(),
            sequence_number=self.sequence_number
        )
        self.current_step = step
        self.steps.append(step)
        return step
    
    def complete_step(self, output: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Complete the current step"""
        if self.current_step:
            self.current_step.completed_at = datetime.utcnow()
            self.current_step.duration_ms = int(
                (self.current_step.completed_at - self.current_step.started_at).total_seconds() * 1000
            )
            if error:
                self.current_step.status = StepStatus.FAILED
                self.current_step.error_message = error
            else:
                self.current_step.status = StepStatus.COMPLETED
                self.current_step.output_data = output
            self.current_step = None
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, 
            source: Optional[str] = None, metadata: Optional[Dict] = None):
        """Add a log entry"""
        log = ExecutionLog(
            id=str(uuid.uuid4()),
            message=message,
            level=level,
            source=source or "system",
            step_id=self.current_step.id if self.current_step else None,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        self.logs.append(log)
    
    def record_tool_call(self, tool_name: str, input_data: Dict, 
                         output_data: Optional[Dict] = None, 
                         duration_ms: int = 0, success: bool = True,
                         error: Optional[str] = None):
        """Record a tool call"""
        call = ToolCall(
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            success=success,
            error=error,
            timestamp=datetime.utcnow()
        )
        self.tool_calls.append(call)
        if self.current_step:
            self.current_step.tool_calls.append(call)
    
    def add_token_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage"""
        self.token_usage.input_tokens += input_tokens
        self.token_usage.output_tokens += output_tokens
        self.token_usage.total_tokens = self.token_usage.input_tokens + self.token_usage.output_tokens


class ExecutionService:
    """Service for executing agents and workflows"""
    
    async def create_execution(
        self,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        trigger_type: str = "manual",
        triggered_by: Optional[str] = None
    ) -> ExecutionResponse:
        """Create a new execution record"""
        doc = execution_to_doc(
            agent_id=agent_id,
            workflow_id=workflow_id,
            input_data=input_data,
            trigger_type=trigger_type,
            triggered_by=triggered_by
        )
        result = await executions_collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc_to_execution(doc)
    
    async def get_by_id(self, execution_id: str) -> Optional[ExecutionResponse]:
        """Get execution by ID"""
        try:
            doc = await executions_collection().find_one({"_id": ObjectId(execution_id)})
            if doc:
                return doc_to_execution(doc)
            return None
        except Exception:
            return None
    
    async def get_detail(self, execution_id: str) -> Optional[ExecutionDetailResponse]:
        """Get execution with steps and logs"""
        execution = await self.get_by_id(execution_id)
        if not execution:
            return None
        
        # Get steps
        steps_cursor = execution_steps_collection().find(
            {"execution_id": execution_id}
        ).sort("sequence_number", 1)
        steps = []
        async for doc in steps_cursor:
            steps.append(doc_to_execution_step(doc))
        
        # Get logs
        logs_cursor = execution_logs_collection().find(
            {"execution_id": execution_id}
        ).sort("timestamp", 1)
        logs = []
        async for doc in logs_cursor:
            logs.append(doc_to_execution_log(doc))
        
        return ExecutionDetailResponse(
            **execution.model_dump(),
            steps=steps,
            logs=logs
        )
    
    async def get_all(
        self,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> ExecutionListResponse:
        """Get all executions with filtering"""
        query = {}
        if agent_id:
            query["agent_id"] = agent_id
        if workflow_id:
            query["workflow_id"] = workflow_id
        if status:
            query["status"] = status.value
        
        total = await executions_collection().count_documents(query)
        
        skip = (page - 1) * per_page
        cursor = executions_collection().find(query).skip(skip).limit(per_page).sort("created_at", -1)
        
        executions = []
        async for doc in cursor:
            executions.append(doc_to_execution(doc))
        
        return ExecutionListResponse(
            executions=executions,
            total=total,
            page=page,
            per_page=per_page
        )
    
    async def update_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None,
        token_usage: Optional[TokenUsage] = None,
        cost_estimate: Optional[float] = None
    ):
        """Update execution status and results"""
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if status == ExecutionStatus.RUNNING:
            update_data["started_at"] = datetime.utcnow()
        
        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            update_data["completed_at"] = datetime.utcnow()
        
        if output_data is not None:
            update_data["output_data"] = output_data
        
        if error_message is not None:
            update_data["error_message"] = error_message
        
        if token_usage:
            update_data["token_usage"] = token_usage.model_dump()
        
        if cost_estimate is not None:
            update_data["cost_estimate"] = cost_estimate
        
        await executions_collection().update_one(
            {"_id": ObjectId(execution_id)},
            {"$set": update_data}
        )
    
    async def save_context(self, execution_id: str, context: ExecutionContext):
        """Save execution steps and logs from context"""
        # Calculate duration
        if context.steps:
            first_step = context.steps[0]
            last_step = context.steps[-1]
            if first_step.started_at and last_step.completed_at:
                duration_ms = int((last_step.completed_at - first_step.started_at).total_seconds() * 1000)
                await executions_collection().update_one(
                    {"_id": ObjectId(execution_id)},
                    {"$set": {"duration_ms": duration_ms}}
                )
        
        # Save steps
        for step in context.steps:
            step_doc = execution_step_to_doc(step, execution_id)
            await execution_steps_collection().insert_one(step_doc)
        
        # Save logs
        for log in context.logs:
            log_doc = execution_log_to_doc(log, execution_id)
            await execution_logs_collection().insert_one(log_doc)
    
    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        trigger_type: str = "manual",
        triggered_by: Optional[str] = None
    ) -> ExecutionDetailResponse:
        """Execute a single agent"""
        # Get agent
        agent = await agent_service.get_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Create execution record
        execution = await self.create_execution(
            agent_id=agent_id,
            input_data=input_data,
            trigger_type=trigger_type,
            triggered_by=triggered_by
        )
        
        context = ExecutionContext(execution.id)
        
        try:
            # Update status to running
            await self.update_status(execution.id, ExecutionStatus.RUNNING)
            context.log(f"Starting execution of agent: {agent.name}", source="system")
            
            # Execute the agent
            output = await self._run_agent(agent, input_data, context)
            
            # Calculate cost estimate
            cost_estimate = self._calculate_cost(context.token_usage, agent.model)
            
            # Update execution with results
            await self.update_status(
                execution.id,
                ExecutionStatus.COMPLETED,
                output_data=output,
                token_usage=context.token_usage,
                cost_estimate=cost_estimate
            )
            
            context.log(f"Execution completed successfully", source="system")
            
        except Exception as e:
            context.log(f"Execution failed: {str(e)}", level=LogLevel.ERROR, source="system")
            await self.update_status(
                execution.id,
                ExecutionStatus.FAILED,
                error_message=str(e),
                token_usage=context.token_usage
            )
        
        # Save steps and logs
        await self.save_context(execution.id, context)
        
        return await self.get_detail(execution.id)
    
    async def _run_agent(
        self,
        agent: AgentResponse,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Run an agent using agenticaiframework primitives.
        This is where we map AgentBuilder config to the framework.
        """
        # Try to use agenticaiframework executor first
        try:
            from app.engine.agentic_executor import AgentBuilderExecutor
            
            # Start agent step
            context.start_step(f"Execute: {agent.name}", "agent", agent.id)
            context.current_step.input_data = input_data
            context.log(f"Using agenticaiframework executor", source="agent")
            
            # Create executor and run
            executor = AgentBuilderExecutor(agent, context)
            result = await executor.execute(input_data)
            
            context.complete_step(output=result)
            return result
            
        except ImportError:
            # Fallback to original executor if agenticaiframework not installed
            from app.engine.executor import AgentExecutor
            
            # Convert to framework config
            framework_config = to_framework_config(agent)
            
            # Start agent step
            context.start_step(f"Execute: {agent.name}", "agent", agent.id)
            context.current_step.input_data = input_data
            context.log(f"Agent configuration (fallback): {framework_config}", source="agent")
            
            try:
                # Create executor and run
                executor = AgentExecutor(agent, context)
                result = await executor.execute(input_data)
                
                context.complete_step(output=result)
                return result
                
            except Exception as e:
                context.complete_step(error=str(e))
                raise
    
    def _calculate_cost(self, token_usage: TokenUsage, model: str) -> float:
        """Calculate cost estimate based on token usage and model"""
        # Approximate pricing (per 1K tokens)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        }
        
        rates = pricing.get(model, pricing["gpt-4"])
        
        input_cost = (token_usage.input_tokens / 1000) * rates["input"]
        output_cost = (token_usage.output_tokens / 1000) * rates["output"]
        
        return round(input_cost + output_cost, 6)


# Global service instance
execution_service = ExecutionService()
