"""
Comprehensive test suite for the PromptTemplates class.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from asabaal_utils.agents.spec_coder.templates import PromptTemplates


class TestPromptTemplates:
    """Test cases for PromptTemplates class."""
    
    @pytest.fixture
    def templates(self):
        """Create a PromptTemplates instance."""
        return PromptTemplates()
    
    def test_init_default(self, templates):
        """Test templates initialization with defaults."""
        assert hasattr(templates, 'source_code_prompt')
        assert hasattr(templates, 'test_prompt')
        assert hasattr(templates, 'documentation_prompt')
        assert len(templates.source_code_prompt) > 0
        assert len(templates.test_prompt) > 0
    
    def test_source_code_prompt_formatting(self, templates):
        """Test source code prompt formatting."""
        formatted = templates.source_code_prompt.format(
            spec_id="test-001",
            title="Test Specification",
            version="1.0.0",
            interfaces="def test_func(): pass",
            requirements="Test requirement"
        )
        
        assert "test-001" in formatted
        assert "def test_func(): pass" in formatted
        assert "Test requirement" in formatted
    
    def test_test_prompt_formatting(self, templates):
        """Test test prompt formatting."""
        formatted = templates.test_prompt.format(
            req_id="req-001",
            req_title="Test Requirement",
            req_description="A test requirement",
            validation="should return True"
        )
        
        assert "req-001" in formatted
        assert "Test Requirement" in formatted
        assert "A test requirement" in formatted
        assert "should return True" in formatted
    
    def test_documentation_prompt_formatting(self, templates):
        """Test documentation prompt formatting."""
        # Check if documentation_prompt exists and can be formatted
        if hasattr(templates, 'documentation_prompt'):
            formatted = templates.documentation_prompt.format(
                spec_id="test-001",
                title="Test Spec",
                requirements="Test requirements"
            )
            
            assert "test-001" in formatted or "Test Spec" in formatted
    
    def test_custom_templates(self):
        """Test creating templates with custom values."""
        custom_templates = PromptTemplates(
            source_code_prompt="Custom source prompt: {spec_id}",
            test_prompt="Custom test prompt: {req_id}"
        )
        
        assert custom_templates.source_code_prompt == "Custom source prompt: {spec_id}"
        assert custom_templates.test_prompt == "Custom test prompt: {req_id}"
    
    def test_template_placeholders(self, templates):
        """Test that templates have expected placeholders."""
        # Source code prompt should have these placeholders
        assert "{spec_id}" in templates.source_code_prompt
        assert "{title}" in templates.source_code_prompt
        assert "{version}" in templates.source_code_prompt
        assert "{interfaces}" in templates.source_code_prompt
        assert "{requirements}" in templates.source_code_prompt
        
        # Test prompt should have these placeholders
        assert "{req_id}" in templates.test_prompt
        assert "{req_title}" in templates.test_prompt
        assert "{req_description}" in templates.test_prompt
        assert "{validation}" in templates.test_prompt
    
    def test_template_content_quality(self, templates):
        """Test that template content is meaningful."""
        # Source code prompt should mention key concepts
        assert "Python" in templates.source_code_prompt
        assert "function" in templates.source_code_prompt.lower()
        
        # Test prompt should mention testing concepts
        assert "pytest" in templates.test_prompt.lower() or "test" in templates.test_prompt.lower()
        assert "generate" in templates.test_prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])