"""
Agent Executor using AgenticAI Framework
Wraps agenticaiframework primitives as a service for the AgentBuilder platform
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import asyncio

from agenticaiframework import Agent, AgentConfig, MemoryManager
from agenticaiframework.tools import SearchTool

from app.core.config import settings
from app.models.agent import AgentResponse
from app.models.execution import LogLevel
from app.services.execution_service import ExecutionContext


class AgentBuilderExecutor:
    """
    Wraps agenticaiframework's Agent class for use in AgentBuilder.
    
    Maps UI configuration to agenticaiframework constructs:
    - Agent form → AgentConfig
    - Tool selection → Tool instances
    - Memory settings → MemoryManager
    - Execution → Agent.execute()
    """
    
    def __init__(self, agent_config: AgentResponse, context: ExecutionContext):
        self.agent_config = agent_config
        self.context = context
        self.memory = MemoryManager()
        self._agent = None
        self._initialize_agent()
    
    def _map_tools(self, tool_names: List[str]):
        """Map tool names from UI to agenticaiframework tool instances"""
        tool_mapping = {
            "web_search": SearchTool,
            "search": SearchTool,
            # Add more tool mappings as needed
        }
        
        tools = []
        for name in tool_names:
            if name in tool_mapping:
                tools.append(tool_mapping[name]())
                self.context.log(f"Registered tool: {name}", source="agent")
        
        return tools
    
    def _initialize_agent(self):
        """Create agenticaiframework Agent from UI configuration"""
        # Map UI config to AgentConfig
        config = AgentConfig(
            name=self.agent_config.name,
            role=self.agent_config.role,
            goal=self.agent_config.goal or f"Complete tasks as {self.agent_config.role}",
            model=self.agent_config.model,
            temperature=self.agent_config.temperature,
            tools=self._map_tools(self.agent_config.tools or [])
        )
        
        # Create the agent with memory
        self._agent = Agent(
            config=config,
            memory=self.memory
        )
        
        self.context.log(
            f"Initialized agenticaiframework Agent: {self.agent_config.name}",
            source="agent",
            metadata={"model": self.agent_config.model, "tools": self.agent_config.tools}
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent using agenticaiframework.
        
        Maps input formats to agent execution and captures observability data.
        """
        # Extract query from various input formats
        query = self._extract_query(input_data)
        
        self.context.log(
            f"Starting execution with agenticaiframework",
            source="agent",
            metadata={"query_length": len(query)}
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Execute using agenticaiframework
            # Run in executor since agenticaiframework may be sync
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._agent.execute(query)
            )
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Extract output from result
            output = result.output if hasattr(result, 'output') else str(result)
            
            # Try to parse as structured JSON
            try:
                parsed_output = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                parsed_output = {"response": output}
            
            # Log token usage if available
            if hasattr(result, 'token_usage'):
                self.context.add_token_usage(
                    result.token_usage.get('input_tokens', 0),
                    result.token_usage.get('output_tokens', 0)
                )
            
            self.context.log(
                f"Execution completed in {duration_ms}ms",
                source="agent"
            )
            
            return {
                "result": parsed_output,
                "raw_response": output,
                "duration_ms": duration_ms,
                "framework": "agenticaiframework",
                "model": self.agent_config.model,
                "token_usage": self.context.token_usage.model_dump()
            }
            
        except Exception as e:
            self.context.log(
                f"Execution failed: {str(e)}",
                level=LogLevel.ERROR,
                source="agent"
            )
            raise
    
    def _extract_query(self, input_data: Dict[str, Any]) -> str:
        """Extract query string from various input formats"""
        if isinstance(input_data, str):
            return input_data
        
        if "query" in input_data:
            return input_data["query"]
        elif "prompt" in input_data:
            return input_data["prompt"]
        elif "task" in input_data:
            task = input_data["task"]
            context = input_data.get("context", "")
            if context:
                return f"{task}\n\nContext: {json.dumps(context)}"
            return task
        elif "messages" in input_data:
            # Extract last user message
            for msg in reversed(input_data["messages"]):
                if msg.get("role") == "user":
                    return msg.get("content", "")
            return ""
        else:
            return json.dumps(input_data)


# Backwards compatibility - use agenticaiframework executor as default
AgentExecutor = AgentBuilderExecutor
