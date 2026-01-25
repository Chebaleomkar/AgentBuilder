"""
Agent Executor
Core execution engine that runs agents using OpenAI/Anthropic APIs
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.agent import AgentResponse
from app.models.execution import LogLevel
from app.services.execution_service import ExecutionContext


class AgentExecutor:
    """
    Executes an agent by:
    1. Building the system prompt from agent config
    2. Calling the LLM with tool definitions
    3. Handling tool calls and responses
    4. Returning structured output
    """
    
    def __init__(self, agent: AgentResponse, context: ExecutionContext):
        self.agent = agent
        self.context = context
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.tools_registry = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize available tools for the agent"""
        from app.engine.tools import get_tool_definitions, get_tool_handlers
        
        # Get tool definitions for the agent's configured tools
        self.tool_definitions = get_tool_definitions(self.agent.tools)
        self.tool_handlers = get_tool_handlers(self.agent.tools)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from agent configuration"""
        base_prompt = self.agent.system_prompt or self.agent.instructions or self.agent.goal
        
        if not base_prompt:
            base_prompt = f"You are {self.agent.name}, a {self.agent.role}."
        
        # Add AgentBuilder personality
        personality = """

You think in structured outputs.
You execute deterministically when possible.
You always validate your work before responding.
When using tools, explain what you're doing.
Return your final response in a clear, structured format."""
        
        return base_prompt + personality
    
    def _build_messages(self, input_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build message history for the LLM"""
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # Handle different input formats
        if "messages" in input_data:
            # Chat-style input
            messages.extend(input_data["messages"])
        elif "query" in input_data:
            # Simple query
            messages.append({"role": "user", "content": input_data["query"]})
        elif "prompt" in input_data:
            # Prompt-based input
            messages.append({"role": "user", "content": input_data["prompt"]})
        elif "task" in input_data:
            # Task-based input
            task = input_data["task"]
            context_str = ""
            if "context" in input_data:
                context_str = f"\n\nContext: {json.dumps(input_data['context'])}"
            messages.append({"role": "user", "content": f"Task: {task}{context_str}"})
        else:
            # Raw input as JSON
            messages.append({"role": "user", "content": json.dumps(input_data)})
        
        return messages
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ) -> Any:
        """Call the LLM with retry logic"""
        kwargs = {
            "model": self.agent.model,
            "messages": messages,
            "temperature": self.agent.temperature,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        
        # Track token usage
        if response.usage:
            self.context.add_token_usage(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
        
        return response
    
    async def _handle_tool_calls(
        self,
        tool_calls: List[Any],
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Handle tool calls from the LLM"""
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            self.context.log(
                f"Calling tool: {tool_name}",
                source="tool",
                metadata={"args": tool_args}
            )
            
            # Start tool step
            self.context.start_step(f"Tool: {tool_name}", "tool")
            self.context.current_step.tool_name = tool_name
            self.context.current_step.input_data = tool_args
            
            start_time = datetime.utcnow()
            
            try:
                # Execute tool
                if tool_name in self.tool_handlers:
                    handler = self.tool_handlers[tool_name]
                    result = await handler(**tool_args)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                self.context.record_tool_call(
                    tool_name=tool_name,
                    input_data=tool_args,
                    output_data=result,
                    duration_ms=duration_ms,
                    success=True
                )
                
                self.context.complete_step(output=result)
                
                # Add tool result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
                
            except Exception as e:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                self.context.record_tool_call(
                    tool_name=tool_name,
                    input_data=tool_args,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                )
                
                self.context.complete_step(error=str(e))
                self.context.log(
                    f"Tool error: {str(e)}",
                    level=LogLevel.ERROR,
                    source="tool"
                )
                
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"error": str(e)})
                })
        
        return messages
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with the given input.
        
        Returns structured output with the agent's response.
        """
        messages = self._build_messages(input_data)
        
        self.context.log(
            f"Starting agent execution with {len(messages)} messages",
            source="agent"
        )
        
        # Determine if we need tools
        tools = self.tool_definitions if self.tool_definitions else None
        
        max_iterations = 10  # Prevent infinite tool loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            self.context.log(
                f"LLM call iteration {iteration}",
                source="agent"
            )
            
            response = await self._call_llm(messages, tools)
            message = response.choices[0].message
            
            # Check if we need to handle tool calls
            if message.tool_calls:
                messages = await self._handle_tool_calls(message.tool_calls, messages)
            else:
                # No more tool calls, return final response
                final_content = message.content or ""
                
                # Try to parse as JSON for structured output
                try:
                    result = json.loads(final_content)
                except json.JSONDecodeError:
                    result = {"response": final_content}
                
                self.context.log(
                    f"Agent completed after {iteration} iterations",
                    source="agent"
                )
                
                return {
                    "result": result,
                    "raw_response": final_content,
                    "iterations": iteration,
                    "token_usage": self.context.token_usage.model_dump()
                }
        
        # Max iterations reached
        raise Exception(f"Agent exceeded maximum iterations ({max_iterations})")
