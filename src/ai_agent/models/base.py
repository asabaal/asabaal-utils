"""
Base model interface for AI Agent Framework.

This module defines the core interface that all model adapters must implement.
"""

import abc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class TokenUsage:
    """Tracks token usage for billing and monitoring."""
    input_tokens: int
    output_tokens: int
    total_cost: float


@dataclass
class ModelResponse:
    """Standardized response format from any model."""
    content: str
    usage: TokenUsage
    model_name: str
    raw_response: Optional[Any] = None


class BaseModel(abc.ABC):
    """Base abstract class for all model adapters.
    
    This class defines the standard interface that all model adapters must
    implement to ensure compatibility with the AI Agent Framework.
    """
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the model."""
        pass
    
    @property
    @abc.abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'Anthropic', 'Google')."""
        pass
    
    @property
    @abc.abstractmethod
    def context_window(self) -> int:
        """Return the maximum context window size in tokens."""
        pass
    
    @property
    @abc.abstractmethod
    def input_cost_per_million_tokens(self) -> float:
        """Return the cost per million input tokens in USD."""
        pass
    
    @property
    @abc.abstractmethod
    def output_cost_per_million_tokens(self) -> float:
        """Return the cost per million output tokens in USD."""
        pass
    
    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from the model.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt/instructions
            temperature: Controls randomness (0-1)
            max_tokens: Maximum response length
            stop_sequences: Optional list of strings that will stop generation
            kwargs: Additional model-specific parameters
            
        Returns:
            A standardized ModelResponse object
        """
        pass
    
    @abc.abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens
        """
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for a given usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            The cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_million_tokens
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_million_tokens
        return input_cost + output_cost
