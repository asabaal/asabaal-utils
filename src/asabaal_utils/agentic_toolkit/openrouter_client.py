"""OpenRouter API client wrapper for structured conversations."""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests

try:
    import openai
except ImportError:
    openai = None


@dataclass
class OpenRouterResponse:
    """Structured response from OpenRouter API."""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str


class OpenRouterClient:
    """Wrapper for OpenRouter API with rate limiting and error handling."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If None, will look for OPENROUTER_API_KEY env var
            model: Model to use (default: anthropic/claude-3.5-sonnet)
        """
        if openai is None:
            raise ImportError(
                "openai package not installed. "
                "Please install with: pip install openai"
            )
        
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError(
                "No API key provided. Please set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        # Use environment variable or default to Qwen 3 Coder Flash
        self.model = model or os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder-flash')
        
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
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
            max_tokens: Optional[int] = None) -> OpenRouterResponse:
        """Send a prompt to OpenRouter and get response.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            OpenRouterResponse with content and metadata
        """
        self._rate_limit()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature
            }
            
            # Add OpenRouter specific headers for better routing
            extra_headers = {
                "HTTP-Referer": "https://github.com/asabaal/asabaal-utils",
                "X-Title": "Asabaal Utils PR Analyzer"
            }
            
            response = self.client.chat.completions.create(
                **kwargs,
                extra_headers=extra_headers
            )
            
            return OpenRouterResponse(
                content=response.choices[0].message.content,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                },
                model=response.model,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            raise Exception(f"OpenRouter API error: {str(e)}")
    
    def ask_json(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.3) -> Dict[str, Any]:
        """Ask OpenRouter for a JSON response.
        
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
    
    def batch_ask(self, prompts: List[str], system_prompt: Optional[str] = None) -> List[OpenRouterResponse]:
        """Send multiple prompts sequentially with rate limiting.
        
        Args:
            prompts: List of prompts to send
            system_prompt: Common system prompt for all requests
            
        Returns:
            List of OpenRouterResponse objects
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
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter."""
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def set_model(self, model: str):
        """Change the model being used."""
        self.model = model
        print(f"🔄 Switched to model: {model}")
    
    def call_agent(self, prompt: str, timeout: int = 300) -> str:
        """Call agent with prompt and return response text.
        
        This method provides compatibility with existing Claude CLI interfaces.
        
        Args:
            prompt: The prompt to send to the agent
            timeout: Timeout in seconds (default: 300)
            
        Returns:
            Response text from the agent
        """
        try:
            response = self.ask(prompt)
            return response.content
        except Exception as e:
            raise Exception(f"OpenRouter agent call failed: {str(e)}")


def create_openrouter_client(model: Optional[str] = None) -> OpenRouterClient:
    """Factory function to create OpenRouter client with default configuration.
    
     Args:
         model: Model to use (default: uses OPENROUTER_MODEL env var or qwen/qwen-2.5-coder-32b-instruct)
        
    Returns:
        Configured OpenRouterClient instance
    """
    return OpenRouterClient(model=model)