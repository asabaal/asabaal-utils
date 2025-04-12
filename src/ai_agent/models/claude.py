"""
Claude model implementation for AI Agent Framework.

This module provides a concrete implementation of the BaseModel interface for Anthropic's Claude models.
"""

import os
from typing import Any, Dict, List, Optional, Union

try:
    import anthropic
except ImportError:
    anthropic = None

from .base import BaseModel, ModelResponse, TokenUsage


class ClaudeModel(BaseModel):
    """Anthropic Claude model implementation.
    
    This class provides a concrete implementation of the BaseModel interface
    for Anthropic's Claude API.
    """
    
    # Model parameter defaults
    DEFAULT_MODEL = "claude-3-7-sonnet-20250219"
    DEFAULT_MAX_TOKENS = 4096
    
    # Current pricing constants
    CLAUDE_3_7_SONNET_INPUT_COST = 3.00  # $ per million tokens
    CLAUDE_3_7_SONNET_OUTPUT_COST = 15.00  # $ per million tokens
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        cache_dir: Optional[str] = None,
    ):
        """Initialize the Claude model adapter.
        
        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
            model_name: Name of Claude model to use
            cache_dir: Optional directory for caching responses
        """
        self._model_name = model_name
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._cache_dir = cache_dir
        
        if not self._api_key:
            raise ValueError(
                "No API key provided. Set the ANTHROPIC_API_KEY environment variable "
                "or pass an api_key parameter."
            )
        
        if not anthropic:
            raise ImportError(
                "The 'anthropic' package is required to use Claude models. "
                "Install it with: pip install anthropic"
            )
        
        # Initialize the client
        self._client = anthropic.Anthropic(api_key=self._api_key)
        
    @property
    def name(self) -> str:
        """Return the name of the model."""
        return self._model_name
    
    @property
    def provider(self) -> str:
        """Return the provider name."""
        return "Anthropic"
    
    @property
    def context_window(self) -> int:
        """Return the maximum context window size in tokens."""
        # Claude 3.7 Sonnet has a 200K token context window
        return 200000
    
    @property
    def input_cost_per_million_tokens(self) -> float:
        """Return the cost per million input tokens in USD."""
        if "claude-3-7-sonnet" in self._model_name:
            return self.CLAUDE_3_7_SONNET_INPUT_COST
        # Add other model pricing as needed
        raise ValueError(f"Unknown pricing for model: {self._model_name}")
    
    @property
    def output_cost_per_million_tokens(self) -> float:
        """Return the cost per million output tokens in USD."""
        if "claude-3-7-sonnet" in self._model_name:
            return self.CLAUDE_3_7_SONNET_OUTPUT_COST
        # Add other model pricing as needed
        raise ValueError(f"Unknown pricing for model: {self._model_name}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from Claude.
        
        Args:
            prompt: The user prompt to send to Claude
            system_prompt: Optional system prompt/instructions
            temperature: Controls randomness (0-1)
            max_tokens: Maximum response length
            stop_sequences: Optional list of strings that will stop generation
            kwargs: Additional Claude-specific parameters
            
        Returns:
            A standardized ModelResponse object
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare Claude parameters
        params = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.DEFAULT_MAX_TOKENS,
            **kwargs
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt
            
        # Add stop sequences if provided
        if stop_sequences:
            params["stop_sequences"] = stop_sequences
        
        # Call the Claude API and get the response
        response = await self._client.messages.create(**params)
        
        # Extract content and usage information
        content = response.content[0].text
        
        # Calculate token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_cost = self.calculate_cost(input_tokens, output_tokens)
        
        # Return standardized response
        return ModelResponse(
            content=content,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost=total_cost
            ),
            model_name=self._model_name,
            raw_response=response
        )
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text using Claude's tokenizer.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens
        """
        return self._client.count_tokens(text)
