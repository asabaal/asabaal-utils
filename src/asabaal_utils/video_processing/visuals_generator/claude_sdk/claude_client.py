"""Claude API client wrapper for structured conversations."""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import time

try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class ClaudeResponse:
    """Structured response from Claude API."""
    content: str
    usage: Dict[str, int]
    model: str
    stop_reason: str


class ClaudeClient:
    """Wrapper for Claude API with rate limiting and error handling."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """Initialize Claude client.
        
        Args:
            api_key: Anthropic API key. If None, will look for ANTHROPIC_API_KEY env var
            model: Model to use (default: claude-3-sonnet-20240229)
        """
        if anthropic is None:
            raise ImportError(
                "anthropic package not installed. "
                "Please install with: pip install anthropic"
            )
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "No API key provided. Please set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = 4096
        self.temperature = 0.7
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # seconds between requests
    
    def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def ask(self, 
            prompt: str, 
            system_prompt: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None) -> ClaudeResponse:
        """Send a prompt to Claude and get response.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            ClaudeResponse with content and metadata
        """
        self._rate_limit()
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            return ClaudeResponse(
                content=response.content[0].text,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                model=response.model,
                stop_reason=response.stop_reason
            )
            
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def ask_json(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.3) -> Dict[str, Any]:
        """Ask Claude for a JSON response.
        
        Args:
            prompt: User prompt (should specify JSON format expected)
            system_prompt: System instructions
            temperature: Lower temperature for more consistent JSON
            
        Returns:
            Parsed JSON response
        """
        json_system = (
            "You are a helpful assistant that responds with valid JSON. "
            "Always format your response as JSON without any markdown formatting."
        )
        
        if system_prompt:
            json_system = f"{json_system}\n\n{system_prompt}"
        
        response = self.ask(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature
        )
        
        try:
            # Clean potential markdown formatting
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nContent: {response.content}")
    
    def batch_ask(self, prompts: List[str], system_prompt: Optional[str] = None) -> List[ClaudeResponse]:
        """Send multiple prompts sequentially with rate limiting.
        
        Args:
            prompts: List of prompts to send
            system_prompt: Common system prompt for all requests
            
        Returns:
            List of ClaudeResponse objects
        """
        responses = []
        for prompt in prompts:
            try:
                response = self.ask(prompt, system_prompt)
                responses.append(response)
            except Exception as e:
                print(f"Error processing prompt: {e}")
                responses.append(None)
        
        return responses