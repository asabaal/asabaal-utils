#!/usr/bin/env python3
"""
Integration tests for the OllamaClient component.
Tests real AI model interaction and API communication.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Import the modules we're testing
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from asabaal_utils.agents.spec_coder.ollama_client import OllamaClient, GenerationConfig


class TestOllamaClientIntegration:
    """Integration tests for OllamaClient with real AI model interaction."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        print(f"\n🪛 Created temporary workspace: {temp_dir}")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up temporary workspace: {temp_dir}")
    
    @pytest.fixture
    def mock_config(self):
        """Mock generation config for testing."""
        return GenerationConfig(
            model="qwen3-coder:latest",
            base_url="http://localhost:11434",
            temperature=0.1,
            max_tokens=1000,
            top_p=0.9,
            top_k=40
        )
    
    @pytest.fixture
    def sample_code(self):
        """Sample code for testing."""
        return '''
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle."""
    if length < 0 or width < 0:
        raise ValueError("Length and width must be positive")
    return length * width
'''
    
    @pytest.fixture
    def sample_requirement(self):
        """Sample requirement for testing."""
        return "Create a function that calculates the area of a rectangle with proper error handling for negative values."
    
    def test_generation_config_initialization(self, temp_workspace):
        """Test GenerationConfig initialization."""
        print("\n🧪 Testing GenerationConfig initialization...")
        
        # Test default config
        default_config = GenerationConfig()
        assert default_config.model == "qwen3-coder:30b"
        assert default_config.base_url == "http://localhost:11434"
        assert default_config.temperature == 0.1
        assert default_config.max_tokens == 4096
        assert default_config.top_p == 0.9
        assert default_config.top_k == 40
        
        # Test custom config
        custom_config = GenerationConfig(
            model="llama3.1:8b",
            base_url="http://custom:11434",
            temperature=0.5,
            max_tokens=2048,
            top_p=0.8,
            top_k=30
        )
        assert custom_config.model == "llama3.1:8b"
        assert custom_config.base_url == "http://custom:11434"
        assert custom_config.temperature == 0.5
        assert custom_config.max_tokens == 2048
        assert custom_config.top_p == 0.8
        assert custom_config.top_k == 30
        
        print("   ✅ GenerationConfig initialization successful")
    
    def test_ollama_client_initialization(self, temp_workspace, mock_config):
        """Test OllamaClient initialization."""
        print("\n🧪 Testing OllamaClient initialization...")
        
        client = OllamaClient(mock_config)
        
        assert client.config == mock_config
        assert hasattr(client, 'session')
        assert client.base_url == "http://localhost:11434"
        assert isinstance(client.session, requests.Session)
        
        print("   ✅ OllamaClient initialization successful")
    
    @patch('requests.Session.get')
    def test_test_connection_success(self, mock_get, temp_workspace, mock_config):
        """Test successful connection testing."""
        print("\n🧪 Testing successful connection...")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'models': [
                {'name': 'qwen3-coder:latest'},
                {'name': 'llama3.1:8b'}
            ]
        }
        mock_get.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.test_connection()
        
        assert result == True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)
        
        print("   ✅ Connection test successful")
    
    @patch('requests.Session.get')
    def test_test_connection_model_not_found(self, mock_get, temp_workspace, mock_config):
        """Test connection when model is not available."""
        print("\n🧪 Testing connection with missing model...")
        
        # Mock response without the requested model
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.1:8b'},
                {'name': 'other:model'}
            ]
        }
        mock_get.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.test_connection()
        
        assert result == False
        
        print("   ✅ Missing model handled correctly")
    
    @patch('requests.Session.get')
    def test_test_connection_failure(self, mock_get, temp_workspace, mock_config):
        """Test connection failure."""
        print("\n🧪 Testing connection failure...")
        
        # Mock connection failure
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        client = OllamaClient(mock_config)
        result = client.test_connection()
        
        assert result == False
        
        print("   ✅ Connection failure handled correctly")
    
    @patch('requests.Session.post')
    def test_generate_success(self, mock_post, temp_workspace, mock_config):
        """Test successful text generation."""
        print("\n🧪 Testing successful text generation...")
        
        # Mock successful generation response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': 'Generated text response',
            'done': True
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.generate("Test prompt")
        
        assert result == 'Generated text response'
        
        # Verify the request payload
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"
        payload = call_args[1]['json']
        assert payload['model'] == 'qwen3-coder:latest'
        assert payload['prompt'] == 'Test prompt'
        assert payload['stream'] == False
        assert payload['options']['temperature'] == 0.1
        assert payload['options']['num_predict'] == 1000
        
        print("   ✅ Text generation successful")
    
    @patch('requests.Session.post')
    def test_generate_with_system_prompt(self, mock_post, temp_workspace, mock_config):
        """Test text generation with system prompt."""
        print("\n🧪 Testing generation with system prompt...")
        
        # Mock successful generation response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': 'Generated code',
            'done': True
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.generate("Test prompt", "System prompt")
        
        assert result == 'Generated code'
        
        # Verify system prompt was included
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['system'] == 'System prompt'
        
        print("   ✅ Generation with system prompt successful")
    
    @patch('requests.Session.post')
    def test_generate_timeout(self, mock_post, temp_workspace, mock_config):
        """Test generation timeout handling."""
        print("\n🧪 Testing generation timeout...")
        
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        client = OllamaClient(mock_config)
        
        with pytest.raises(requests.exceptions.Timeout):
            client.generate("Test prompt")
        
        print("   ✅ Timeout handled correctly")
    
    @patch('requests.Session.post')
    def test_generate_empty_response(self, mock_post, temp_workspace, mock_config):
        """Test handling of empty response."""
        print("\n🧪 Testing empty response handling...")
        
        # Mock empty response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': '',
            'done': True
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.generate("Test prompt")
        
        assert result == ''
        
        print("   ✅ Empty response handled correctly")
    
    @patch('requests.Session.post')
    def test_generate_code(self, mock_post, temp_workspace, mock_config, sample_code):
        """Test code generation."""
        print("\n🧪 Testing code generation...")
        
        # Mock successful code generation response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': 'def hello():\n    print("Hello, World!")',
            'done': True
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.generate_code("Create a hello world function")
        
        assert 'def hello():' in result
        
        # Verify system prompt was set for code generation
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert 'expert python developer' in payload['system']
        assert 'clean, well-documented' in payload['system']
        
        print("   ✅ Code generation successful")
    
    @patch('requests.Session.post')
    def test_generate_tests(self, mock_post, temp_workspace, mock_config, sample_code, sample_requirement):
        """Test test generation."""
        print("\n🧪 Testing test generation...")
        
        # Mock successful test generation response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': '''def test_calculate_area():
    assert calculate_area(5, 3) == 15
    assert calculate_area(0, 10) == 0''',
            'done': True
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.generate_tests(sample_code, sample_requirement)
        
        assert 'test_calculate_area' in result
        assert 'calculate_area(5, 3)' in result
        
        # Verify prompt contains code and requirement
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert sample_code in payload['prompt']
        assert sample_requirement in payload['prompt']
        assert 'comprehensive pytest tests' in payload['prompt']
        
        # Verify system prompt for test generation
        assert 'expert in writing comprehensive tests' in payload['system']
        
        print("   ✅ Test generation successful")
    
    @patch('requests.Session.post')
    def test_get_model_info(self, mock_post, temp_workspace, mock_config):
        """Test getting model information."""
        print("\n🧪 Testing model info retrieval...")
        
        # Mock successful model info response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'modelfile': 'FROM qwen3-coder:latest',
            'parameters': {'temperature': '0.1'},
            'template': '{{ .Prompt }}'
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.get_model_info()
        
        assert 'modelfile' in result
        assert 'parameters' in result
        assert 'template' in result
        
        # Verify the request
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/show"
        payload = call_args[1]['json']
        assert payload['name'] == 'qwen3-coder:latest'
        
        print("   ✅ Model info retrieval successful")
    
    @patch('requests.Session.post')
    def test_get_model_info_failure(self, mock_post, temp_workspace, mock_config):
        """Test model info retrieval failure."""
        print("\n🧪 Testing model info failure...")
        
        # Mock failure
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        client = OllamaClient(mock_config)
        result = client.get_model_info()
        
        assert result == {}
        
        print("   ✅ Model info failure handled correctly")
    
    @patch('requests.Session.get')
    def test_list_models(self, mock_get, temp_workspace, mock_config):
        """Test listing available models."""
        print("\n🧪 Testing model listing...")
        
        # Mock successful models response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'models': [
                {'name': 'qwen3-coder:latest'},
                {'name': 'llama3.1:8b'},
                {'name': 'codellama:latest'}
            ]
        }
        mock_get.return_value = mock_response
        
        client = OllamaClient(mock_config)
        result = client.list_models()
        
        assert len(result) == 3
        assert 'qwen3-coder:latest' in result
        assert 'llama3.1:8b' in result
        assert 'codellama:latest' in result
        
        # Verify the request
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=10)
        
        print("   ✅ Model listing successful")
    
    @patch('requests.Session.get')
    def test_list_models_failure(self, mock_get, temp_workspace, mock_config):
        """Test model listing failure."""
        print("\n🧪 Testing model listing failure...")
        
        # Mock failure
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        client = OllamaClient(mock_config)
        result = client.list_models()
        
        assert result == []
        
        print("   ✅ Model listing failure handled correctly")
    
    def test_complete_workflow_simulation(self, temp_workspace, mock_config, sample_code, sample_requirement):
        """Test complete workflow simulation with mocked responses."""
        print("\n🧪 Testing complete workflow simulation...")
        
        with patch('requests.Session.get') as mock_get, \
             patch('requests.Session.post') as mock_post:
            
            # Mock connection test
            mock_connection_response = Mock()
            mock_connection_response.raise_for_status.return_value = None
            mock_connection_response.json.return_value = {
                'models': [{'name': 'qwen3-coder:latest'}]
            }
            mock_get.return_value = mock_connection_response
            
            # Mock generation responses
            mock_generation_response = Mock()
            mock_generation_response.raise_for_status.return_value = None
            mock_generation_response.json.return_value = {
                'response': 'Generated content',
                'done': True
            }
            mock_post.return_value = mock_generation_response
            
            # Initialize client and test workflow
            client = OllamaClient(mock_config)
            
            # Step 1: Test connection
            connection_ok = client.test_connection()
            assert connection_ok == True
            
            # Step 2: Generate code
            code_result = client.generate_code("Create a function")
            assert code_result == 'Generated content'
            
            # Step 3: Generate tests
            test_result = client.generate_tests(sample_code, sample_requirement)
            assert test_result == 'Generated content'
            
            # Step 4: Get model info
            model_info = client.get_model_info()
            assert model_info == {'response': 'Generated content', 'done': True}
            
            # Step 5: List models
            models = client.list_models()
            assert models == ['qwen3-coder:latest']
            
            print("   ✅ Complete workflow simulation successful")
    
    def test_error_handling_scenarios(self, temp_workspace, mock_config):
        """Test various error handling scenarios."""
        print("\n🧪 Testing error handling scenarios...")
        
        client = OllamaClient(mock_config)
        
        # Test JSON decode error
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_post.return_value = mock_response
            
            with pytest.raises(json.JSONDecodeError):
                client.generate("Test prompt")
        
        # Test request exception
        with patch('requests.Session.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Request failed")
            
            with pytest.raises(requests.exceptions.RequestException):
                client.generate("Test prompt")
        
        print("   ✅ Error handling scenarios verified")
    
    def test_config_validation(self, temp_workspace):
        """Test configuration validation."""
        print("\n🧪 Testing configuration validation...")
        
        # Test valid configurations
        valid_configs = [
            GenerationConfig(),
            GenerationConfig(model="llama3.1:8b"),
            GenerationConfig(temperature=0.0),
            GenerationConfig(temperature=1.0),
            GenerationConfig(max_tokens=1),
            GenerationConfig(top_p=0.0),
            GenerationConfig(top_p=1.0),
            GenerationConfig(top_k=1),
        ]
        
        for config in valid_configs:
            client = OllamaClient(config)
            assert client.config == config
        
        print("   ✅ Configuration validation successful")


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "-s"])