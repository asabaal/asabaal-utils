"""Backend configuration for agentic toolkit - supports OpenRouter and Ollama."""

import os
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass


class BackendType(Enum):
    """Available backend types."""
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    CLAUDE = "claude"


@dataclass
class BackendConfig:
    """Configuration for an AI backend."""
    backend_type: BackendType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 300
    temperature: float = 0.7
    max_tokens: int = 4096


class BackendManager:
    """Manages multiple AI backends with fallback support."""
    
    def __init__(self, config: Optional[BackendConfig] = None):
        """Initialize backend manager.
        
        Args:
            config: Specific backend config to use. If None, will auto-detect.
        """
        self.config = config or self._auto_detect_config()
        self.client = None
        self._initialize_client()
    
    def _auto_detect_config(self) -> BackendConfig:
        """Auto-detect the best available backend configuration."""
        
        # Priority 1: Check for explicit backend preference
        backend_env = os.getenv('AGENTIC_BACKEND', '').lower()
        
        if backend_env == 'ollama':
            return BackendConfig(
                backend_type=BackendType.OLLAMA,
                model=os.getenv('OLLAMA_MODEL', 'qwen3-coder:latest'),
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                timeout=int(os.getenv('OLLAMA_TIMEOUT', '300'))
            )
        
        elif backend_env == 'openrouter':
            return BackendConfig(
                backend_type=BackendType.OPENROUTER,
                model=os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder-flash'),
                api_key=os.getenv('OPENROUTER_API_KEY')
            )
        
        elif backend_env == 'claude':
            return BackendConfig(
                backend_type=BackendType.CLAUDE,
                model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
            )
        
        # Priority 2: Auto-detect based on available credentials/services
        
        # Check for Ollama first (local, no API key needed)
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                return BackendConfig(
                    backend_type=BackendType.OLLAMA,
                    model=os.getenv('OLLAMA_MODEL', 'qwen3-coder:latest'),
                    base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                )
        except:
            pass
        
        # Check for OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            return BackendConfig(
                backend_type=BackendType.OPENROUTER,
                model=os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder-flash'),
                api_key=os.getenv('OPENROUTER_API_KEY')
            )
        
        # Check for Claude
        if os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY'):
            return BackendConfig(
                backend_type=BackendType.CLAUDE,
                model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
                api_key=os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
            )
        
        # Fallback: Default to OpenRouter but will fail gracefully
        return BackendConfig(
            backend_type=BackendType.OPENROUTER,
            model='qwen/qwen3-coder-flash',
            api_key=os.getenv('OPENROUTER_API_KEY')
        )
    
    def _initialize_client(self):
        """Initialize the appropriate client based on configuration."""
        try:
            if self.config.backend_type == BackendType.OLLAMA:
                from .ollama_client import OllamaClient
                self.client = OllamaClient(
                    model=self.config.model,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout
                )
                
            elif self.config.backend_type == BackendType.OPENROUTER:
                from .openrouter_client import OpenRouterClient
                self.client = OpenRouterClient(
                    api_key=self.config.api_key,
                    model=self.config.model
                )
                
            elif self.config.backend_type == BackendType.CLAUDE:
                # For now, fallback to OpenRouter with Claude model
                from .openrouter_client import OpenRouterClient
                self.client = OpenRouterClient(
                    api_key=self.config.api_key,
                    model=self.config.model
                )
                
        except Exception as e:
            print(f"⚠️  Failed to initialize {self.config.backend_type.value} client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if the backend client is available and working."""
        return self.client is not None
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend configuration."""
        return {
            'backend_type': self.config.backend_type.value,
            'model': self.config.model,
            'base_url': self.config.base_url,
            'timeout': self.config.timeout,
            'available': self.is_available(),
            'api_key_present': bool(self.config.api_key)
        }
    
    def call_agent(self, prompt: str, **kwargs) -> str:
        """Call the agent with the given prompt.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments passed to the client
            
        Returns:
            Response text from the agent
        """
        if not self.client:
            raise RuntimeError(f"Backend {self.config.backend_type.value} not available")
        
        return self.client.call_agent(prompt, **kwargs)
    
    def ask(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Any:
        """Ask the backend a question.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional arguments
            
        Returns:
            Backend-specific response object
        """
        if not self.client:
            raise RuntimeError(f"Backend {self.config.backend_type.value} not available")
        
        return self.client.ask(prompt, system_prompt, **kwargs)
    
    def ask_json(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Ask for a JSON response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional arguments
            
        Returns:
            Parsed JSON response
        """
        if not self.client:
            raise RuntimeError(f"Backend {self.config.backend_type.value} not available")
        
        return self.client.ask_json(prompt, system_prompt, **kwargs)
    
    def switch_backend(self, backend_type: Union[str, BackendType], **kwargs):
        """Switch to a different backend.
        
        Args:
            backend_type: New backend type
            **kwargs: Additional configuration for the new backend
        """
        if isinstance(backend_type, str):
            backend_type = BackendType(backend_type.lower())
        
        # Create new config
        if backend_type == BackendType.OLLAMA:
            new_config = BackendConfig(
                backend_type=backend_type,
                model=kwargs.get('model', os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:32b')),
                base_url=kwargs.get('base_url', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')),
                timeout=kwargs.get('timeout', int(os.getenv('OLLAMA_TIMEOUT', '300')))
            )
        elif backend_type == BackendType.OPENROUTER:
            new_config = BackendConfig(
                backend_type=backend_type,
                model=kwargs.get('model', os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder-flash')),
                api_key=kwargs.get('api_key', os.getenv('OPENROUTER_API_KEY'))
            )
        elif backend_type == BackendType.CLAUDE:
            new_config = BackendConfig(
                backend_type=backend_type,
                model=kwargs.get('model', os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')),
                api_key=kwargs.get('api_key', os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
            )
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
        
        self.config = new_config
        self._initialize_client()
        
        print(f"🔄 Switched to {backend_type.value} backend with model {new_config.model}")


def create_backend_manager(backend_type: Optional[str] = None, **kwargs) -> BackendManager:
    """Factory function to create a backend manager.
    
    Args:
        backend_type: Specific backend type to use
        **kwargs: Additional configuration arguments
        
    Returns:
        Configured BackendManager instance
    """
    if backend_type:
        config = None  # Will be created by BackendManager with explicit type
        manager = BackendManager(config)
        if backend_type.lower() != manager.config.backend_type.value:
            manager.switch_backend(backend_type, **kwargs)
        return manager
    
    return BackendManager()


def list_available_backends() -> Dict[str, Dict[str, Any]]:
    """List all available backends and their status.
    
    Returns:
        Dictionary mapping backend names to their availability info
    """
    backends = {}
    
    # Check Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            backends['ollama'] = {
                'available': True,
                'models': [m['name'] for m in models],
                'base_url': 'http://localhost:11434'
            }
        else:
            backends['ollama'] = {'available': False}
    except:
        backends['ollama'] = {'available': False}
    
    # Check OpenRouter
    if os.getenv('OPENROUTER_API_KEY'):
        backends['openrouter'] = {
            'available': True,
            'api_key_present': True,
            'default_model': os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder-flash')
        }
    else:
        backends['openrouter'] = {'available': False, 'api_key_present': False}
    
    # Check Claude
    if os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY'):
        backends['claude'] = {
            'available': True,
            'api_key_present': True,
            'default_model': os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        }
    else:
        backends['claude'] = {'available': False, 'api_key_present': False}
    
    return backends


if __name__ == "__main__":
    # Test backend detection
    print("Available backends:")
    for name, info in list_available_backends().items():
        status = "✅" if info['available'] else "❌"
        print(f"  {status} {name}: {info}")
    
    print("\nCreating backend manager...")
    manager = create_backend_manager()
    print(f"Selected backend: {manager.get_backend_info()}")