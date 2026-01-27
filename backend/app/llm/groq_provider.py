"""
GROQ LLM Provider Adapter.

Provides integration with GROQ's ultra-fast inference API including:
- Llama 3.1 and 3.3 models  
- Tool/Function calling
- Streaming support
"""

import os
import logging
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class GroqProviderConfig:
    """Configuration for GROQ provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "llama-3.3-70b-versatile",
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries


class GroqResponse:
    """Standardized response from GROQ."""
    
    def __init__(
        self,
        content: str,
        model: str,
        finish_reason: str = "stop",
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        usage: Optional[Dict[str, int]] = None,
        raw_response: Optional[Any] = None
    ):
        self.content = content
        self.model = model
        self.provider = "groq"
        self.finish_reason = finish_reason
        self.tool_calls = tool_calls
        self.usage = usage or {}
        self.raw_response = raw_response
    
    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


class GroqProvider:
    """
    GROQ API provider adapter.
    
    Supports ultra-fast inference with:
    - llama-3.3-70b-versatile (best quality)  
    - llama-3.1-8b-instant (fastest)
    
    Example:
        >>> provider = GroqProvider.from_env()
        >>> response = provider.generate("Hello, world!")
        >>> print(response.content)
    """
    
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    
    SUPPORTED_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile", 
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]
    
    def __init__(self, config: Optional[GroqProviderConfig] = None):
        self.config = config or GroqProviderConfig()
        self._client = None
        self._initialized = False
    
    @classmethod
    def from_env(cls, model: Optional[str] = None) -> 'GroqProvider':
        """Create provider from environment variables."""
        # Try to get from settings first, then fall back to os.getenv
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try:
                from app.core.config import settings
                api_key = getattr(settings, 'GROQ_API_KEY', None)
            except Exception:
                pass
        
        config = GroqProviderConfig(
            api_key=api_key,
            default_model=model or os.getenv("GROQ_MODEL", cls.DEFAULT_MODEL),
            timeout=float(os.getenv("GROQ_TIMEOUT", "60")),
        )
        return cls(config)
    
    @property
    def provider_name(self) -> str:
        return "groq"
    
    @property
    def supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS
    
    def _initialize_client(self) -> None:
        """Initialize GROQ client."""
        try:
            from groq import Groq
            
            self._client = Groq(api_key=self.config.api_key)
            logger.info("GROQ client initialized with model: %s", self.config.default_model)
        except ImportError:
            raise ImportError(
                "GROQ package not installed. "
                "Install with: pip install groq"
            )
        except Exception as e:
            logger.error("Failed to initialize GROQ client: %s", e)
            raise
    
    def _ensure_initialized(self) -> None:
        """Ensure the client is initialized."""
        if not self._initialized:
            self._initialize_client()
            self._initialized = True
    
    def is_available(self) -> bool:
        """Check if GROQ is configured."""
        return bool(self.config.api_key)
    
    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> GroqResponse:
        """Generate text using GROQ API."""
        self._ensure_initialized()
        
        model_name = model or self.config.default_model
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            completion_kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens
            if stop:
                completion_kwargs["stop"] = stop
            
            response = self._client.chat.completions.create(**completion_kwargs)
            
            content = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason or "stop"
            
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return GroqResponse(
                content=content,
                model=model_name,
                finish_reason=finish_reason,
                usage=usage,
                raw_response=response,
            )
        except Exception as e:
            logger.error("GROQ generation failed: %s", e)
            raise
    
    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> GroqResponse:
        """Generate from chat messages."""
        self._ensure_initialized()
        
        model_name = model or self.config.default_model
        
        try:
            completion_kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens
            
            response = self._client.chat.completions.create(**completion_kwargs)
            
            content = response.choices[0].message.content or ""
            
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return GroqResponse(
                content=content,
                model=model_name,
                finish_reason=response.choices[0].finish_reason or "stop",
                usage=usage,
                raw_response=response,
            )
        except Exception as e:
            logger.error("GROQ chat generation failed: %s", e)
            raise
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> GroqResponse:
        """Generate with function/tool calling."""
        self._ensure_initialized()
        
        model_name = model or self.config.default_model
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Convert tools to OpenAI-compatible format (GROQ uses same format)
        formatted_tools = []
        for tool in tools:
            if "function" in tool:
                formatted_tools.append(tool)
            else:
                formatted_tools.append({
                    "type": "function",
                    "function": tool
                })
        
        try:
            response = self._client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=formatted_tools if formatted_tools else None,
                temperature=temperature,
            )
            
            message = response.choices[0].message
            content = message.content or ""
            
            tool_calls = None
            if message.tool_calls:
                tool_calls = []
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    })
            
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return GroqResponse(
                content=content,
                model=model_name,
                finish_reason=response.choices[0].finish_reason or "stop",
                tool_calls=tool_calls,
                usage=usage,
                raw_response=response,
            )
        except Exception as e:
            logger.error("GROQ tool generation failed: %s", e)
            raise


__all__ = ['GroqProvider', 'GroqProviderConfig', 'GroqResponse']
