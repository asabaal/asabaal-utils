"""
Model adapters for the AI Agent Framework.

This module provides standardized interfaces for different LLM providers,
allowing the framework to work with multiple AI models.
"""

from .base import BaseModel
from .claude import ClaudeModel

__all__ = ["BaseModel", "ClaudeModel"]
