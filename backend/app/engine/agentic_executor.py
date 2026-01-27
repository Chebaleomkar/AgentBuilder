"""
Agent Executor with Multi-Provider LLM Support

Wraps agenticaiframework primitives with fallback to direct LLM calls.
Supports Google Gemini, GROQ, and OpenAI providers.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import asyncio
import logging
import os

from app.core.config import settings
from app.models.agent import AgentResponse
from app.models.execution import LogLevel
from app.services.execution_service import ExecutionContext

logger = logging.getLogger(__name__)


# Tool implementations
class WebSearchTool:
    """Web search tool using DuckDuckGo."""
    
    name = "web_search"
    description = "Search the web for information"
    
    def __init__(self):
        self._search = None
    
    def _ensure_initialized(self):
        if self._search is None:
            try:
                from duckduckgo_search import DDGS
                self._search = DDGS()
            except ImportError:
                raise ImportError("duckduckgo-search not installed. Run: pip install duckduckgo-search")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform a web search and return results."""
        self._ensure_initialized()
        try:
            results = list(self._search.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return []


class TextSummarizerTool:
    """Text summarization tool using LLM."""
    
    name = "text_summarizer"
    description = "Summarize text content"
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize the given text."""
        # This will be handled by the LLM directly
        return text[:max_length] + "..." if len(text) > max_length else text


# Tool registry
TOOL_REGISTRY = {
    "web_search": WebSearchTool,
    "search": WebSearchTool,
    "text_summarizer": TextSummarizerTool,
}


class AgentBuilderExecutor:
    """
    Executes agents using the best available LLM provider.
    
    Features:
    - Multi-provider support (Gemini, GROQ, OpenAI)
    - Tool calling with web search
    - Automatic fallback between providers
    - Full observability logging
    """
    
    def __init__(self, agent_config: AgentResponse, context: ExecutionContext):
        self.agent_config = agent_config
        self.context = context
        self.tools = self._initialize_tools(agent_config.tools or [])
        self._llm_service = None
    
    def _get_llm_service(self):
        """Get the LLM service (lazy initialization)."""
        if self._llm_service is None:
            from app.llm.providers import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service
    
    def _initialize_tools(self, tool_names: List[str]) -> Dict[str, Any]:
        """Initialize requested tools."""
        tools = {}
        for name in tool_names:
            if name in TOOL_REGISTRY:
                try:
                    tools[name] = TOOL_REGISTRY[name]()
                    self.context.log(f"Initialized tool: {name}", source="agent")
                except Exception as e:
                    self.context.log(f"Failed to initialize tool {name}: {e}", level=LogLevel.WARNING, source="agent")
        return tools
    
    def _get_model_and_provider(self) -> tuple:
        """Determine the best model and provider to use."""
        model = self.agent_config.model
        llm_service = self._get_llm_service()
        available = llm_service.available_providers
        
        # Map model to preferred provider
        if model.startswith("gemini"):
            preferred_provider = "gemini"
        elif model.startswith("llama") or model.startswith("mixtral"):
            preferred_provider = "groq"
        elif model.startswith("gpt"):
            preferred_provider = "openai"
        else:
            preferred_provider = None
        
        # Check if preferred provider is available
        if preferred_provider and preferred_provider in available:
            return model, preferred_provider
        
        # Fallback to the active provider with its default model
        active_provider = llm_service.active_provider_name
        if active_provider:
            # Use the active provider's default model
            default_model = llm_service.MODEL_MAPPINGS.get(active_provider, {}).get("default")
            self.context.log(
                f"Provider '{preferred_provider}' not available, using '{active_provider}' with model '{default_model}'",
                source="agent"
            )
            return default_model or model, active_provider
        
        # Last resort - return what we have
        return model, None

    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent using the best available LLM.
        
        Supports:
        - Direct prompts
        - Tool-augmented execution (web search, etc.)
        - Multi-step reasoning
        """
        query = self._extract_query(input_data)
        model, provider = self._get_model_and_provider()
        
        self.context.log(
            f"Starting execution with model: {model}",
            source="agent",
            metadata={"provider": provider, "tools": list(self.tools.keys())}
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Build the complete prompt with agent context
            system_prompt = self._build_system_prompt()
            full_prompt = self._build_execution_prompt(query)
            
            # Execute tool calls if needed
            tool_results = {}
            if self.tools and "web_search" in self.tools:
                # Perform web search for research-type queries
                self.context.log("Executing web search tool...", source="tool")
                search_tool = self.tools["web_search"]
                search_results = search_tool.search(query, max_results=5)
                tool_results["web_search"] = search_results
                
                # Add search results to prompt
                if search_results:
                    search_context = "\n\nWeb Search Results:\n"
                    for i, r in enumerate(search_results, 1):
                        search_context += f"{i}. {r['title']}\n   URL: {r['url']}\n   {r['snippet']}\n\n"
                    full_prompt += search_context
            
            # Get LLM response
            llm_service = self._get_llm_service()
            
            self.context.log(
                f"Calling LLM with provider: {llm_service.active_provider_name}",
                source="agent"
            )
            
            response = llm_service.generate(
                full_prompt,
                provider=provider,
                model=model if model and not model.startswith("gpt") else None,  # Let service pick if OpenAI
                temperature=self.agent_config.temperature,
                system_prompt=system_prompt,
            )
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Extract and parse output
            output = response.get("content", "")
            
            try:
                parsed_output = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                parsed_output = {"response": output}
            
            # Log token usage
            usage = response.get("usage", {})
            if usage:
                self.context.add_token_usage(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )
            
            self.context.log(
                f"Execution completed in {duration_ms}ms using {response.get('provider', 'unknown')}",
                source="agent"
            )
            
            return {
                "result": parsed_output,
                "raw_response": output,
                "duration_ms": duration_ms,
                "provider": response.get("provider"),
                "model": response.get("model"),
                "tool_results": tool_results if tool_results else None,
                "token_usage": self.context.token_usage.model_dump()
            }
            
        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.context.log(
                f"Execution failed after {duration_ms}ms: {str(e)}",
                level=LogLevel.ERROR,
                source="agent"
            )
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from agent configuration."""
        return f"""You are {self.agent_config.name}, a {self.agent_config.role}.

Goal: {self.agent_config.goal or 'Complete the given task efficiently.'}

{self.agent_config.instructions or ''}

Respond in a clear, structured format. When providing research or analysis, include:
- Key findings
- Supporting evidence
- Sources (if available)
- Recommendations (if applicable)"""
    
    def _build_execution_prompt(self, query: str) -> str:
        """Build the execution prompt."""
        return f"""Task: {query}

Please complete this task thoroughly and provide a comprehensive response."""
    
    def _extract_query(self, input_data: Dict[str, Any]) -> str:
        """Extract query string from various input formats."""
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


# Backwards compatibility
AgentExecutor = AgentBuilderExecutor


__all__ = ['AgentBuilderExecutor', 'AgentExecutor', 'WebSearchTool', 'TextSummarizerTool']
