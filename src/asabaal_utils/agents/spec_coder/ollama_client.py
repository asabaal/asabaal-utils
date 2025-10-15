"""
Ollama Client Wrapper

Provides a clean interface for interacting with Ollama models,
specifically configured for code generation tasks.
"""

import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for model generation."""
    model: str = "qwen3-coder:30b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    max_tokens: int = 4096
    top_p: float = 0.9
    top_k: int = 40


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.session = requests.Session()
        self.base_url = config.base_url.rstrip('/')
    
    def test_connection(self) -> bool:
        """Test if Ollama is accessible and model is available."""
        try:
            # Check if Ollama is running
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.config.model not in model_names:
                logger.warning(f"Model {self.config.model} not found. Available models: {model_names}")
                return False
            
            logger.info(f"Successfully connected to Ollama with model {self.config.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from the model."""
        # Prepare the request payload
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_predict": self.config.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.debug(f"Sending generation request to {self.config.model}")
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minute timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('response', '')
            
            if not generated_text:
                logger.warning("Model returned empty response")
                return ""
            
            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text
            
        except requests.exceptions.Timeout:
            logger.error("Generation request timed out")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode response: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            raise
    
    def generate_code(self, prompt: str, language: str = "python") -> str:
        """Generate code with appropriate system prompt."""
        system_prompt = f"""You are an expert {language} developer. Generate clean, well-documented, and functional code.

Follow these guidelines:
- Write complete, working code (no TODO placeholders)
- Include proper error handling
- Add type hints where appropriate
- Write clear docstrings
- Follow {language} best practices and conventions
- Ensure the code is testable and maintainable

Return only the code without explanations unless specifically asked."""
        
        return self.generate(prompt, system_prompt)
    
    def generate_tests(self, code: str, requirement_description: str) -> str:
        """Generate tests for given code and requirement."""
        prompt = f"""Generate comprehensive pytest tests for the following code and requirement:

Requirement:
{requirement_description}

Code to test:
```python
{code}
```

Generate tests that verify:
- Correct functionality and happy paths
- Edge cases and boundary conditions
- Error handling and invalid inputs
- Type safety where applicable

Return only the test code without explanations."""
        
        system_prompt = """You are an expert in writing comprehensive tests. Generate thorough pytest test suites that cover all aspects of the code including normal operation, edge cases, and error conditions."""
        
        return self.generate(prompt, system_prompt)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": self.config.model},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
    
    def list_models(self) -> List[str]:
        """List all available models."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []