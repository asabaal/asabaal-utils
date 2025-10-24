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
    """
    Client for interacting with Ollama API for AI-powered code generation and analysis.
    
    This class provides a clean, robust interface for communicating with Ollama models,
    specifically optimized for code generation, test analysis, and specification processing
    tasks. It handles connection management, error recovery, and response processing.
    
    The client supports various generation modes including code generation, test creation,
    and general text analysis with configurable parameters for temperature, tokens, and
    other model settings.
    
    Attributes:
        config: GenerationConfig containing model settings and parameters
        session: Requests session for HTTP communication with Ollama
        base_url: Base URL for Ollama API endpoints
    
    Example:
        >>> config = GenerationConfig(model="qwen3-coder:latest", temperature=0.1)
        >>> client = OllamaClient(config)
        >>> if client.test_connection():
        ...     response = client.generate("Write a Python function to add two numbers")
        ...     print(response)
    """
    
    def __init__(self, config: GenerationConfig):
        """
        Initialize the OllamaClient with configuration.
        
        Args:
            config: GenerationConfig object containing model name, base URL, temperature,
                   max_tokens, and other generation parameters.
        
        Raises:
            ValueError: If config is None or contains invalid settings
        
        Example:
            >>> config = GenerationConfig(
            ...     model="qwen3-coder:latest",
            ...     base_url="http://localhost:11434",
            ...     temperature=0.1,
            ...     max_tokens=2048
            ... )
            >>> client = OllamaClient(config)
        """
        self.config = config
        self.session = requests.Session()
        self.base_url = config.base_url.rstrip('/')
    
    def test_connection(self) -> bool:
        """
        Test if Ollama server is accessible and the configured model is available.
        
        This method performs a two-step verification:
        1. Checks if Ollama server is running and accessible
        2. Verifies that the specified model is available in the server
        
        Returns:
            True if both server and model are accessible, False otherwise.
        
        Raises:
            requests.exceptions.ConnectionError: If Ollama server is not reachable
            requests.exceptions.Timeout: If connection times out
        
        Example:
            >>> client = OllamaClient(config)
            >>> if client.test_connection():
            ...     print("Ollama is ready")
            ... else:
            ...     print("Ollama is not available")
        """
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
        """
        Generate text response using the configured Ollama model.
        
        This is the core generation method that sends prompts to the Ollama API
        and returns the model's response. It supports both simple prompts and
        prompts with system instructions for better control over output format.
        
        Args:
            prompt: The main prompt text to send to the model. This should contain
                   the specific task or question for the model to address.
            system_prompt: Optional system prompt to set the model's behavior and
                          response format. Useful for controlling output style,
                          format requirements, or role-playing scenarios.
        
        Returns:
            Generated text response from the model as a string.
        
        Raises:
            requests.exceptions.ConnectionError: If Ollama server is not reachable
            requests.exceptions.Timeout: If generation times out
            ValueError: If prompt is empty or invalid
            RuntimeError: If model returns an error response
        
        Example:
            >>> client = OllamaClient(config)
            >>> # Simple generation
            >>> response = client.generate("Explain recursion in simple terms")
            >>> print(response)
            >>> 
            >>> # Generation with system prompt
            >>> response = client.generate(
            ...     "Write a function to calculate factorial",
            ...     system_prompt="You are a Python programming expert. Provide clean, well-documented code."
            ... )
            >>> print(response)
        """
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
                timeout=300  # 5 minute timeout
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
        """
        Generate code in a specified programming language using optimized prompts.
        
        This method is specifically optimized for code generation tasks. It automatically
        formats the prompt with appropriate system instructions to generate clean,
        well-structured code in the specified programming language.
        
        Args:
            prompt: Description of the code to generate. Should include requirements,
                   function signatures, expected behavior, and any constraints.
            language: Programming language for code generation. Defaults to "python".
                     Common options include "python", "javascript", "java", "cpp", etc.
        
        Returns:
            Generated code as a string. The code is typically formatted with proper
            indentation and may include comments or docstrings depending on the language.
        
        Raises:
            ValueError: If language is not supported or prompt is insufficient
            RuntimeError: If code generation fails or returns invalid content
        
        Example:
            >>> client = OllamaClient(config)
            >>> code = client.generate_code(
            ...     "Create a function that validates email addresses using regex",
            ...     language="python"
            ... )
            >>> print(code)
            >>> 
            >>> # Generate JavaScript code
            >>> js_code = client.generate_code(
            ...     "Create a function that sorts an array of objects by a property",
            ...     language="javascript"
            ... )
            >>> print(js_code)
        """
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
        """
        Generate comprehensive tests for given code based on requirement description.
        
        This method analyzes the provided code and requirement description to generate
        appropriate test cases. It considers normal operation, edge cases, error conditions,
        and validation criteria to create thorough test coverage.
        
        Args:
            code: Source code for which tests should be generated. This can be a single
                  function, class, or module that needs testing.
            requirement_description: Description of what the code should do, including
                                   expected behavior, inputs, outputs, and any special
                                   requirements or constraints.
        
        Returns:
            Generated test code as a string, typically including multiple test functions
            with different scenarios and assertions. The format depends on the language
            of the input code (assumes Python for Python code, etc.).
        
        Raises:
            ValueError: If code is empty or requirement description is insufficient
            RuntimeError: If test generation fails or returns invalid test code
        
        Example:
            >>> client = OllamaClient(config)
            >>> code = '''
            ... def add_numbers(a, b):
            ...     return a + b
            ... '''
            >>> requirement = "Function should add two numbers and handle non-numeric inputs"
            >>> tests = client.generate_tests(code, requirement)
            >>> print(tests)
            >>> 
            >>> # Expected output might include:
            >>> # - Test normal addition
            >>> # - Test with negative numbers
            >>> # - Test with non-numeric inputs (error handling)
            >>> # - Test edge cases (zero, large numbers)
        """
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