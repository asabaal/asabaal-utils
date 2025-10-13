"""Ollama client wrapper for local model inference."""

import os
import json
import time
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests


@dataclass
class OllamaResponse:
    """Structured response from Ollama API."""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    response_time_ms: float


class OllamaClient:
    """Wrapper for Ollama local API with error handling and compatibility."""
    
    def __init__(self, 
                 model: Optional[str] = None, 
                 base_url: Optional[str] = None,
                 timeout: int = 300):
        """Initialize Ollama client.
        
        Args:
            model: Model to use (default: qwen2.5-coder:32b)
            base_url: Ollama API base URL (default: http://localhost:11434)
            timeout: Request timeout in seconds
        """
        self.model = model or os.getenv('OLLAMA_MODEL', 'qwen3-coder:latest')
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.timeout = timeout
        self.max_tokens = 4096
        self.temperature = 0.7
        
        # Verify ollama is available
        self._verify_ollama_available()
        
        print(f"🔧 Ollama client initialized:")
        print(f"   Model: {self.model}")
        print(f"   Base URL: {self.base_url}")
        print(f"   Timeout: {timeout}s")
    
    def _verify_ollama_available(self):
        """Verify that ollama is running and model is available."""
        try:
            # Check if ollama service is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if not any(self.model in name for name in model_names):
                available_models = ', '.join(model_names[:5])  # Show first 5
                if len(model_names) > 5:
                    available_models += f" ... and {len(model_names) - 5} more"
                
                raise ValueError(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Available models: {available_models}\n"
                    f"Pull the model with: ollama pull {self.model}"
                )
                
            print(f"✅ Ollama service verified with {len(models)} models available")
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: 'ollama serve'"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama verification failed: {e}")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Ollama API."""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Failed to connect to Ollama at {self.base_url}")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def ask(self, 
            prompt: str, 
            system_prompt: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None) -> OllamaResponse:
        """Send a prompt to Ollama and get response.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            OllamaResponse with content and metadata
        """
        start_time = time.time()
        
        # Build the prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant: "
        else:
            full_prompt = f"User: {prompt}\n\nAssistant: "
        
        data = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            }
        }
        
        try:
            response_data = self._make_request("generate", data)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract usage info if available
            usage = {
                "prompt_tokens": response_data.get("prompt_eval_count", 0),
                "output_tokens": response_data.get("eval_count", 0),
                "total_tokens": response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)
            }
            
            return OllamaResponse(
                content=response_data.get("response", ""),
                usage=usage,
                model=response_data.get("model", self.model),
                finish_reason=response_data.get("done_reason", "stop"),
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            raise Exception(f"Ollama generation error: {str(e)}")
    
    def ask_json(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.3) -> Dict[str, Any]:
        """Ask Ollama for a JSON response.
        
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
    
    def batch_ask(self, prompts: List[str], system_prompt: Optional[str] = None) -> List[OllamaResponse]:
        """Send multiple prompts sequentially.
        
        Args:
            prompts: List of prompts to send
            system_prompt: Common system prompt for all requests
            
        Returns:
            List of OllamaResponse objects
        """
        responses = []
        for i, prompt in enumerate(prompts):
            try:
                print(f"Processing prompt {i+1}/{len(prompts)}...")
                response = self.ask(prompt, system_prompt)
                responses.append(response)
            except Exception as e:
                print(f"Error processing prompt {i+1}: {e}")
                responses.append(None)
        
        return responses
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama."""
        try:
            response_data = self._make_request("tags", {})
            return response_data.get('models', [])
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def set_model(self, model: str):
        """Change the model being used."""
        self.model = model
        self._verify_ollama_available()  # Verify new model is available
        print(f"🔄 Switched to model: {model}")
    
    def call_agent(self, prompt: str, timeout: Optional[int] = None) -> str:
        """Call agent with prompt and return response text.
        
        This method provides compatibility with existing Claude/OpenRouter interfaces.
        
        Args:
            prompt: The prompt to send to the agent
            timeout: Override default timeout
            
        Returns:
            Response text from the agent
        """
        original_timeout = None
        if timeout:
            original_timeout = self.timeout
            self.timeout = timeout
        
        try:
            response = self.ask(prompt)
            return response.content
        except Exception as e:
            raise Exception(f"Ollama agent call failed: {str(e)}")
        finally:
            if original_timeout is not None:
                self.timeout = original_timeout
    
    def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry.
        
        Args:
            model: Model name to pull
            
        Returns:
            True if successful, False otherwise
        """
        print(f"📥 Pulling model {model}... (this may take a while)")
        
        try:
            # Use subprocess to show progress
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully pulled model {model}")
                return True
            else:
                print(f"❌ Failed to pull model {model}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Pulling model {model} timed out")
            return False
        except FileNotFoundError:
            print("❌ 'ollama' command not found. Install Ollama first.")
            return False
        except Exception as e:
            print(f"❌ Error pulling model {model}: {e}")
            return False


def create_ollama_client(model: Optional[str] = None) -> OllamaClient:
    """Factory function to create Ollama client with default configuration.
    
    Args:
        model: Model to use (default: uses OLLAMA_MODEL env var or qwen2.5-coder:32b)
        
    Returns:
        Configured OllamaClient instance
    """
    return OllamaClient(model=model)


def test_ollama_connection(model: str = "qwen2.5-coder:32b") -> bool:
    """Test Ollama connection with a simple prompt.
    
    Args:
        model: Model to test with
        
    Returns:
        True if connection works, False otherwise
    """
    try:
        client = OllamaClient(model=model)
        response = client.ask("Hello! Can you respond with just 'OK'?", temperature=0.1)
        
        if "OK" in response.content.upper():
            print(f"✅ Ollama connection test successful with {model}")
            print(f"   Response: {response.content.strip()}")
            print(f"   Response time: {response.response_time_ms:.0f}ms")
            return True
        else:
            print(f"⚠️  Ollama responded but not as expected: {response.content.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the client if run directly
    print("Testing Ollama client...")
    test_ollama_connection()