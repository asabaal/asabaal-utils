"""
Comprehensive test suite for the OllamaClient class.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from requests import Response

from asabaal_utils.agents.spec_coder.ollama_client import OllamaClient, GenerationConfig


class TestGenerationConfig:
    """Test cases for GenerationConfig dataclass."""
    
    def test_generation_config_defaults(self):
        """Test GenerationConfig with default values."""
        config = GenerationConfig()
        
        assert config.model == "qwen3-coder:30b"
        assert config.base_url == "http://localhost:11434"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.top_p == 0.9
        assert config.top_k == 40
    
    def test_generation_config_custom_values(self):
        """Test GenerationConfig with custom values."""
        config = GenerationConfig(
            model="custom-model",
            base_url="http://custom:8080",
            temperature=0.5,
            max_tokens=2048,
            top_p=0.8,
            top_k=30
        )
        
        assert config.model == "custom-model"
        assert config.base_url == "http://custom:8080"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.top_p == 0.8
        assert config.top_k == 30


class TestOllamaClient:
    """Test cases for OllamaClient class."""
    
    @pytest.fixture
    def config(self):
        """Create a test GenerationConfig."""
        return GenerationConfig(
            model="test-model",
            base_url="http://test:11434",
            temperature=0.7,
            max_tokens=1000
        )
    
    @pytest.fixture
    def client(self, config):
        """Create an OllamaClient instance with test config."""
        return OllamaClient(config)
    
    def test_init(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.base_url == "http://test:11434"
        assert hasattr(client, 'session')
    
    def test_base_url_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        config = GenerationConfig(base_url="http://test:11434/")
        client = OllamaClient(config)
        assert client.base_url == "http://test:11434"
    
    @patch('requests.Session.get')
    def test_connection_success(self, mock_get, client):
        """Test successful connection test."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'models': [
                {'name': 'test-model'},
                {'name': 'other-model'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = client.test_connection()
        
        assert result is True
        mock_get.assert_called_once_with(
            "http://test:11434/api/tags",
            timeout=5
        )
    
    @patch('requests.Session.get')
    def test_connection_failure_ollama_down(self, mock_get, client):
        """Test connection failure when Ollama is down."""
        # Mock failed response
        mock_get.side_effect = Exception("Connection failed")
        
        result = client.test_connection()
        
        assert result is False
    
    @patch('requests.Session.get')
    def test_connection_model_not_available(self, mock_get, client):
        """Test connection when model is not available."""
        # Mock response with different models
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'models': [
                {'name': 'other-model'},
                {'name': 'another-model'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = client.test_connection()
        
        assert result is False
    
    @patch('requests.Session.post')
    def test_generate_success(self, mock_post, client):
        """Test successful generation."""
        # Mock successful generation response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': 'Generated code',
            'done': True
        }
        mock_post.return_value = mock_response
        
        prompt = "Generate a function"
        result = client.generate(prompt)
        
        assert result == 'Generated code'
        mock_post.assert_called_once()
        
        # Check the request data
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test:11434/api/generate"
        request_data = call_args[1]['json']
        assert request_data['model'] == 'test-model'
        assert request_data['prompt'] == prompt
        assert request_data['options']['temperature'] == 0.7
        assert request_data['options']['num_predict'] == 1000
    
    def test_generate_with_system_prompt(self, client):
        """Test generation with system prompt."""
        with patch.object(client.session, 'post') as mock_post:
            # Mock successful generation response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'response': 'Generated code',
                'done': True
            }
            mock_post.return_value = mock_response
            
            prompt = "Generate a function"
            system_prompt = "You are a Python expert"
            result = client.generate(prompt, system_prompt=system_prompt)
            
            assert result == 'Generated code'
            
            # Check the request data
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            assert request_data['system'] == system_prompt
    
    @patch('requests.Session.post')
    def test_generate_failure(self, mock_post, client):
        """Test generation failure."""
        # Mock failed response
        mock_post.side_effect = Exception("Generation failed")
        
        prompt = "Generate a function"
        
        with pytest.raises(Exception, match="Generation failed"):
            client.generate(prompt)
    
    
    
    def test_generate_code(self, client):
        """Test code generation with system prompt."""
        with patch.object(client, 'generate') as mock_generate:
            mock_generate.return_value = "def test(): pass"
            
            result = client.generate_code("Write a test function")
            
            assert result == "def test(): pass"
            mock_generate.assert_called_once()
            
            # Check that system prompt was included
            call_args = mock_generate.call_args
            assert "python developer" in call_args[0][1]  # system prompt
            assert call_args[0][0] == "Write a test function"  # user prompt
    
    def test_generate_tests(self, client):
        """Test test generation."""
        with patch.object(client, 'generate') as mock_generate:
            mock_generate.return_value = "def test_code(): pass"
            
            code = "def add(a, b): return a + b"
            requirement = "Add two numbers"
            
            result = client.generate_tests(code, requirement)
            
            assert result == "def test_code(): pass"
            mock_generate.assert_called_once()
            
            # Check that the prompt contains both code and requirement
            call_args = mock_generate.call_args
            prompt = call_args[0][0]
            assert code in prompt
            assert requirement in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])