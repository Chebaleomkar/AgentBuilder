"""
Agent Executor
Core execution engine that runs agents using OpenAI and Google Gemini APIs
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.agent import AgentResponse
from app.models.execution import LogLevel
from app.services.execution_service import ExecutionContext


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GEMINI = "gemini"


def get_provider_for_model(model: str) -> LLMProvider:
    """Determine which provider to use based on model name"""
    if model in settings.GEMINI_MODELS or model.startswith("gemini"):
        return LLMProvider.GEMINI
    return LLMProvider.OPENAI


class OpenAIExecutor:
    """OpenAI-specific execution logic"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        
        # Extract response data
        message = response.choices[0].message
        
        return {
            "content": message.content or "",
            "tool_calls": message.tool_calls if hasattr(message, 'tool_calls') else None,
            "usage": {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        }


class GeminiExecutor:
    """Google Gemini-specific execution logic"""
    
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.genai = genai
    
    def _convert_messages_to_gemini(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert OpenAI-style messages to Gemini format"""
        system_instruction = None
        history = []
        current_message = None
        
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                current_message = content
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content or ""]})
            elif role == "tool":
                # Add tool response as user message
                history.append({"role": "user", "parts": [f"Tool result: {content}"]})
        
        # Remove the last user message as it will be sent separately
        if history and history[-1]["role"] == "user":
            current_message = history.pop()["parts"][0]
        
        return system_instruction, history, current_message
    
    def _convert_tools_to_gemini(self, tools: List[Dict]) -> Optional[List]:
        """Convert OpenAI-style tools to Gemini function declarations"""
        if not tools:
            return None
        
        from google.generativeai.types import FunctionDeclaration, Tool
        
        function_declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                fd = FunctionDeclaration(
                    name=func["name"],
                    description=func.get("description", ""),
                    parameters=func.get("parameters", {})
                )
                function_declarations.append(fd)
        
        if function_declarations:
            return [Tool(function_declarations=function_declarations)]
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Call Gemini API"""
        system_instruction, history, current_message = self._convert_messages_to_gemini(messages)
        
        # Create the model with system instruction
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": 8192,
        }
        
        model_instance = self.genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system_instruction
        )
        
        # Start chat with history
        chat = model_instance.start_chat(history=history if history else [])
        
        # Convert tools if present
        gemini_tools = self._convert_tools_to_gemini(tools) if tools else None
        
        # Send message
        if gemini_tools:
            response = await chat.send_message_async(current_message, tools=gemini_tools)
        else:
            response = await chat.send_message_async(current_message)
        
        # Check for function calls
        tool_calls = None
        content = ""
        
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    # Convert to OpenAI-like tool call format
                    if tool_calls is None:
                        tool_calls = []
                    
                    # Create a mock tool call object
                    class MockFunction:
                        def __init__(self, name, arguments):
                            self.name = name
                            self.arguments = arguments
                    
                    class MockToolCall:
                        def __init__(self, func_name, func_args):
                            self.id = f"call_{datetime.utcnow().timestamp()}"
                            self.function = MockFunction(func_name, json.dumps(dict(func_args)))
                    
                    tool_calls.append(MockToolCall(
                        part.function_call.name,
                        part.function_call.args
                    ))
                elif hasattr(part, 'text'):
                    content += part.text
        
        # Estimate token usage (Gemini doesn't always provide this)
        input_tokens = len(str(messages)) // 4  # Rough estimate
        output_tokens = len(content) // 4
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        }


class AgentExecutor:
    """
    Executes an agent by:
    1. Building the system prompt from agent config
    2. Calling the LLM (OpenAI or Gemini) with tool definitions
    3. Handling tool calls and responses
    4. Returning structured output
    """
    
    def __init__(self, agent: AgentResponse, context: ExecutionContext):
        self.agent = agent
        self.context = context
        self.provider = get_provider_for_model(agent.model)
        
        # Initialize the appropriate executor
        if self.provider == LLMProvider.GEMINI:
            self.llm_executor = GeminiExecutor()
            self.context.log(f"Using Gemini provider for model: {agent.model}", source="agent")
        else:
            self.llm_executor = OpenAIExecutor()
            self.context.log(f"Using OpenAI provider for model: {agent.model}", source="agent")
        
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
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Call the LLM (OpenAI or Gemini)"""
        response = await self.llm_executor.call(
            model=self.agent.model,
            messages=messages,
            temperature=self.agent.temperature,
            tools=tools
        )
        
        # Track token usage
        self.context.add_token_usage(
            response["usage"]["input_tokens"],
            response["usage"]["output_tokens"]
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
            f"Starting agent execution with {len(messages)} messages using {self.provider.value}",
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
            
            # Check if we need to handle tool calls
            if response["tool_calls"]:
                messages = await self._handle_tool_calls(response["tool_calls"], messages)
            else:
                # No more tool calls, return final response
                final_content = response["content"]
                
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
                    "provider": self.provider.value,
                    "model": self.agent.model,
                    "token_usage": self.context.token_usage.model_dump()
                }
        
        # Max iterations reached
        raise Exception(f"Agent exceeded maximum iterations ({max_iterations})")
