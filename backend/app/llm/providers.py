"""
Multi-Provider LLM Service

Unified interface for multiple LLM providers with automatic fallback:
1. Google Gemini (primary if GEMINI_API_KEY exists)
2. GROQ (secondary/fallback if GROQ_API_KEY exists)
3. OpenAI (fallback if OPENAI_API_KEY exists)

Automatically selects the best available provider based on environment.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service with multi-provider support.
    
    Automatically detects available providers and routes requests.
    Supports fallback chains for reliability.
    """
    
    # Provider priority order
    PROVIDER_PRIORITY = ["groq","gemini","openai"]
    
    # Model mappings for each provider
    MODEL_MAPPINGS = {
        "gemini": {
            "default": "gemini-1.5-flash",
            "high_quality": "gemini-1.5-pro",
            "fast": "gemini-1.5-flash",
            "vision": "gemini-1.5-pro",
        },
        "groq": {
            "default": "llama-3.3-70b-versatile",
            "high_quality": "llama-3.3-70b-versatile",
            "fast": "llama-3.1-8b-instant",
            "vision": None,  # GROQ doesn't support vision yet
        },
        "openai": {
            "default": "gpt-4o-mini",
            "high_quality": "gpt-4o",
            "fast": "gpt-3.5-turbo",
            "vision": "gpt-4o",
        }
    }
    
    def __init__(self):
        self._providers = {}
        self._active_provider = None
        self._fallback_chain = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available providers."""
        registered = []
        
        # Try Google Gemini
        gemini_key = settings.GEMINI_API_KEY
        if gemini_key and gemini_key != "your-gemini-api-key-here":
            try:
                from agenticaiframework.llms.providers import GoogleProvider
                provider = GoogleProvider.from_env()
                self._providers["gemini"] = provider
                registered.append("gemini")
                logger.info("Registered Gemini provider")
            except Exception as e:
                logger.warning("Failed to initialize Gemini provider: %s", e)
        
        # Try GROQ - prioritize GROQ
        groq_key = settings.GROQ_API_KEY if hasattr(settings, 'GROQ_API_KEY') else os.getenv("GROQ_API_KEY")
        if groq_key and groq_key not in ["", "your-groq-api-key-here"]:
            try:
                from app.llm.groq_provider import GroqProvider
                provider = GroqProvider.from_env()
                self._providers["groq"] = provider
                registered.append("groq")
                logger.info("Registered GROQ provider with key: %s...", groq_key[:10])
            except Exception as e:
                logger.warning("Failed to initialize GROQ provider: %s", e)
        
        # Try OpenAI (only if key is set and not placeholder)
        openai_key = settings.OPENAI_API_KEY
        if openai_key and openai_key != "your-openai-api-key-here":
            try:
                from agenticaiframework.llms.providers import OpenAIProvider
                provider = OpenAIProvider.from_env()
                self._providers["openai"] = provider
                registered.append("openai")
                logger.info("Registered OpenAI provider")
            except Exception as e:
                logger.warning("Failed to initialize OpenAI provider: %s", e)
        
        # Set active provider based on priority
        for provider_name in self.PROVIDER_PRIORITY:
            if provider_name in registered:
                self._active_provider = provider_name
                break
        
        # Set fallback chain
        self._fallback_chain = [p for p in self.PROVIDER_PRIORITY if p in registered]
        
        if registered:
            logger.info(
                "LLM Service initialized. Active: %s, Fallback chain: %s",
                self._active_provider,
                self._fallback_chain
            )
        else:
            logger.warning(
                "No LLM providers available! Set GEMINI_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY"
            )
    
    @property
    def active_provider_name(self) -> Optional[str]:
        """Get the name of the active provider."""
        return self._active_provider
    
    @property
    def available_providers(self) -> List[str]:
        """List available provider names."""
        return list(self._providers.keys())
    
    def get_provider(self, name: Optional[str] = None):
        """Get a specific provider instance."""
        if name is None:
            name = self._active_provider
        return self._providers.get(name)
    
    def get_model_for_task(self, task_type: str = "default") -> tuple:
        """
        Get the best model for a task type.
        
        Args:
            task_type: One of 'default', 'high_quality', 'fast', 'vision'
            
        Returns:
            Tuple of (provider_name, model_name)
        """
        if not self._active_provider:
            return None, None
        
        model_name = self.MODEL_MAPPINGS.get(
            self._active_provider, {}
        ).get(task_type, self.MODEL_MAPPINGS[self._active_provider]["default"])
        
        return self._active_provider, model_name
    
    def generate(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using the best available provider.
        
        Args:
            prompt: Input prompt
            provider: Specific provider to use (optional)
            model: Specific model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: System instruction (optional)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict with 'content', 'model', 'provider', 'usage'
        """
        provider_name = provider or self._active_provider
        if not provider_name:
            raise ValueError("No LLM provider available")
        
        # Try providers in fallback order
        providers_to_try = [provider_name] if provider else self._fallback_chain
        
        last_error = None
        for pname in providers_to_try:
            try:
                llm_provider = self._providers.get(pname)
                if not llm_provider:
                    continue
                
                # Use provider's default model if not specified
                model_to_use = model
                if not model_to_use:
                    model_to_use = self.MODEL_MAPPINGS.get(pname, {}).get("default")
                
                # Handle GROQ differently (uses our custom provider)
                if pname == "groq":
                    response = llm_provider.generate(
                        prompt,
                        model=model_to_use,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                        **kwargs
                    )
                else:
                    # agenticaiframework providers
                    response = llm_provider.generate(
                        prompt,
                        model=model_to_use,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                
                return {
                    "content": response.content,
                    "model": response.model,
                    "provider": pname,
                    "usage": response.usage if hasattr(response, 'usage') else {},
                    "finish_reason": getattr(response, 'finish_reason', 'stop'),
                }
                
            except Exception as e:
                logger.warning("Provider %s failed: %s", pname, e)
                last_error = e
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate with tool/function calling support.
        
        Args:
            prompt: Input prompt
            tools: List of tool schemas
            provider: Specific provider to use
            model: Specific model to use
            temperature: Sampling temperature
            
        Returns:
            Dict with 'content', 'tool_calls', 'model', 'provider'
        """
        provider_name = provider or self._active_provider
        if not provider_name:
            raise ValueError("No LLM provider available")
        
        llm_provider = self._providers.get(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not available")
        
        model_to_use = model or self.MODEL_MAPPINGS.get(provider_name, {}).get("default")
        
        try:
            if provider_name == "groq":
                response = llm_provider.generate_with_tools(
                    prompt,
                    tools,
                    model=model_to_use,
                    temperature=temperature,
                    **kwargs
                )
            else:
                response = llm_provider.generate_with_tools(
                    prompt,
                    tools,
                    model=model_to_use,
                    temperature=temperature,
                    **kwargs
                )
            
            return {
                "content": response.content,
                "tool_calls": response.tool_calls,
                "model": response.model,
                "provider": provider_name,
                "usage": response.usage if hasattr(response, 'usage') else {},
            }
        except Exception as e:
            logger.error("Tool generation failed: %s", e)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status and available providers."""
        return {
            "active_provider": self._active_provider,
            "available_providers": list(self._providers.keys()),
            "fallback_chain": self._fallback_chain,
            "models": {
                name: self.MODEL_MAPPINGS.get(name, {})
                for name in self._providers.keys()
            }
        }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def reset_llm_service() -> None:
    """Reset the LLM service singleton (useful after env var changes)."""
    global _llm_service
    _llm_service = None


__all__ = ['LLMService', 'get_llm_service', 'reset_llm_service']
