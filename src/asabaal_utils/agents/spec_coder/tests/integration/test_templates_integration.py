#!/usr/bin/env python3
"""
Integration tests for the Templates component.
Tests AI-driven documentation generation and prompt templates.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Import the modules we're testing
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from asabaal_utils.agents.spec_coder.templates import PromptTemplates


class TestTemplatesIntegration:
    """Integration tests for PromptTemplates with real AI workflows."""
    
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
    def sample_openspec(self):
        """Sample OpenSpec specification for testing."""
        return {
            "spec_id": "RPG-001",
            "title": "Rhythmic Pulse Generator",
            "description": "Generates deterministic rhythmic patterns",
            "requirements": [
                {
                    "id": "RPG-001-01",
                    "title": "Generate Time Grid",
                    "description": "Generate time grid based on BPM and time signature",
                    "validation": "Output should contain correct beat positions",
                    "interfaces": [
                        {
                            "name": "generate_time_grid",
                            "parameters": [
                                {"name": "bpm", "type": "int"},
                                {"name": "time_signature", "type": "str"},
                                {"name": "bars", "type": "int"}
                            ],
                            "return_type": "list[float]"
                        }
                    ]
                },
                {
                    "id": "RPG-001-02", 
                    "title": "Apply Accent Pattern",
                    "description": "Apply accent patterns to time grid",
                    "validation": "Output should preserve grid structure",
                    "interfaces": [
                        {
                            "name": "apply_accent_pattern",
                            "parameters": [
                                {"name": "grid", "type": "list[float]"},
                                {"name": "pattern", "type": "list[int]"}
                            ],
                            "return_type": "list[tuple[float, int]]"
                        }
                    ]
                }
            ]
        }
    
    @pytest.mark.integration
    def test_prompt_templates_initialization(self, temp_workspace):
        """Test PromptTemplates initialization."""
        print("\n🧪 Testing PromptTemplates initialization...")
        
        templates = PromptTemplates()
        
        # Check that all templates are present
        assert hasattr(templates, 'source_code_prompt')
        assert hasattr(templates, 'test_prompt')
        assert hasattr(templates, 'documentation_prompt')
        assert hasattr(templates, 'system_prompt')
        
        # Check that templates are strings
        assert isinstance(templates.source_code_prompt, str)
        assert isinstance(templates.test_prompt, str)
        assert isinstance(templates.documentation_prompt, str)
        assert isinstance(templates.system_prompt, str)
        
        # Check that templates contain expected placeholders
        assert '{spec_id}' in templates.source_code_prompt
        assert '{interfaces}' in templates.source_code_prompt
        assert '{requirements}' in templates.source_code_prompt
        
        assert '{req_id}' in templates.test_prompt
        assert '{req_title}' in templates.test_prompt
        assert '{req_description}' in templates.test_prompt
        assert '{validation}' in templates.test_prompt
        
        assert '{spec_id}' in templates.documentation_prompt
        assert '{title}' in templates.documentation_prompt
        assert '{requirements}' in templates.documentation_prompt
        
        print("   ✅ PromptTemplates initialization successful")
    
    @pytest.mark.integration
    def test_source_code_prompt_generation(self, temp_workspace, sample_openspec):
        """Test source code prompt generation from OpenSpec."""
        print("\n🧪 Testing source code prompt generation...")
        
        templates = PromptTemplates()
        
        # Extract interfaces and requirements from OpenSpec
        interfaces = []
        requirements = []
        
        for req in sample_openspec["requirements"]:
            requirements.append(f"- {req['id']}: {req['description']}")
            for interface in req.get("interfaces", []):
                params = ", ".join([f"{p['name']}: {p['type']}" for p in interface["parameters"]])
                interfaces.append(f"{interface['name']}({params}) -> {interface['return_type']}")
        
        # Generate the prompt
        prompt = templates.source_code_prompt.format(
            spec_id=sample_openspec["spec_id"],
            interfaces="\n".join(interfaces),
            requirements="\n".join(requirements)
        )
        
        # Verify prompt content
        assert sample_openspec["spec_id"] in prompt
        assert "generate_time_grid" in prompt
        assert "apply_accent_pattern" in prompt
        assert "bpm: int" in prompt
        assert "time_signature: str" in prompt
        assert "bars: int" in prompt
        assert "list[float]" in prompt
        assert "RPG-001-01" in prompt
        assert "RPG-001-02" in prompt
        
        print("   ✅ Source code prompt generated successfully")
        print(f"   📝 Prompt length: {len(prompt)} characters")
    
    @pytest.mark.integration
    def test_test_prompt_generation(self, temp_workspace, sample_openspec):
        """Test test prompt generation from requirement."""
        print("\n🧪 Testing test prompt generation...")
        
        templates = PromptTemplates()
        
        # Use first requirement for testing
        requirement = sample_openspec["requirements"][0]
        
        # Generate the prompt
        prompt = templates.test_prompt.format(
            req_id=requirement["id"],
            req_title=requirement["title"],
            req_description=requirement["description"],
            validation=requirement["validation"]
        )
        
        # Verify prompt content
        assert requirement["id"] in prompt
        assert requirement["title"] in prompt
        assert requirement["description"] in prompt
        assert requirement["validation"] in prompt
        assert "comprehensive pytest tests" in prompt
        assert "Edge cases" in prompt
        assert "Error conditions" in prompt
        assert "Type safety" in prompt
        
        print("   ✅ Test prompt generated successfully")
        print(f"   📝 Prompt length: {len(prompt)} characters")
    
    @pytest.mark.integration
    def test_documentation_prompt_generation(self, temp_workspace, sample_openspec):
        """Test documentation prompt generation from OpenSpec."""
        print("\n🧪 Testing documentation prompt generation...")
        
        templates = PromptTemplates()
        
        # Extract requirements text
        requirements_text = "\n".join([
            f"- {req['id']}: {req['description']}" 
            for req in sample_openspec["requirements"]
        ])
        
        # Generate the prompt
        prompt = templates.documentation_prompt.format(
            spec_id=sample_openspec["spec_id"],
            title=sample_openspec["title"],
            requirements=requirements_text
        )
        
        # Verify prompt content
        assert sample_openspec["spec_id"] in prompt
        assert sample_openspec["title"] in prompt
        assert "RPG-001-01" in prompt
        assert "RPG-001-02" in prompt
        assert "Project overview" in prompt
        assert "Installation instructions" in prompt
        assert "Usage examples" in prompt
        assert "API documentation" in prompt
        assert "Requirements traceability" in prompt
        
        print("   ✅ Documentation prompt generated successfully")
        print(f"   📝 Prompt length: {len(prompt)} characters")
    
    @pytest.mark.integration
    def test_system_prompt_content(self, temp_workspace):
        """Test system prompt content."""
        print("\n🧪 Testing system prompt content...")
        
        templates = PromptTemplates()
        
        # Verify system prompt content
        assert "Python scaffolding code" in templates.system_prompt
        assert "function stubs" in templates.system_prompt
        assert "TODO comments" in templates.system_prompt
        assert "pass statements" in templates.system_prompt
        assert "NOT implement actual functionality" in templates.system_prompt
        
        print("   ✅ System prompt content verified")
    
    @patch('asabaal_utils.agents.spec_coder.templates.PromptTemplates')
    @pytest.mark.integration
    def test_template_integration_with_generator(self, mock_templates_class, temp_workspace, sample_openspec):
        """Test template integration with code generation workflow."""
        print("\n🧪 Testing template integration with generator...")
        
        # Mock the templates
        mock_templates = Mock()
        mock_templates.source_code_prompt = "Mock source code prompt with {spec_id}"
        mock_templates_class.return_value = mock_templates
        
        # Simulate generator workflow
        from asabaal_utils.agents.spec_coder.templates import PromptTemplates
        
        templates = PromptTemplates()
        
        # Format prompt with OpenSpec data
        prompt = templates.source_code_prompt.format(
            spec_id=sample_openspec["spec_id"],
            interfaces="generate_time_grid(bpm: int, time_signature: str, bars: int) -> list[float]",
            requirements="- RPG-001-01: Generate time grid"
        )
        
        # Verify integration
        assert sample_openspec["spec_id"] in prompt
        
        print("   ✅ Template integration with generator successful")
    
    @pytest.mark.integration
    def test_template_customization(self, temp_workspace):
        """Test template customization capabilities."""
        print("\n🧪 Testing template customization...")
        
        # Create custom templates
        custom_templates = PromptTemplates(
            source_code_prompt="Custom source prompt: {spec_id}",
            test_prompt="Custom test prompt: {req_id}",
            documentation_prompt="Custom docs: {spec_id}",
            system_prompt="Custom system prompt"
        )
        
        # Test customization
        assert custom_templates.source_code_prompt == "Custom source prompt: {spec_id}"
        assert custom_templates.test_prompt == "Custom test prompt: {req_id}"
        assert custom_templates.documentation_prompt == "Custom docs: {spec_id}"
        assert custom_templates.system_prompt == "Custom system prompt"
        
        # Test formatting
        prompt = custom_templates.source_code_prompt.format(spec_id="TEST-001")
        assert prompt == "Custom source prompt: TEST-001"
        
        print("   ✅ Template customization successful")
    
    @pytest.mark.integration
    def test_template_error_handling(self, temp_workspace):
        """Test template error handling."""
        print("\n🧪 Testing template error handling...")
        
        templates = PromptTemplates()
        
        # Test missing placeholder
        with pytest.raises(KeyError):
            templates.source_code_prompt.format(
                spec_id="TEST-001"
                # Missing interfaces and requirements
            )
        
        # Test with empty data
        try:
            prompt = templates.source_code_prompt.format(
                spec_id="",
                interfaces="",
                requirements=""
            )
            assert isinstance(prompt, str)
        except Exception as e:
            print(f"   ⚠️  Expected error with empty data: {e}")
        
        print("   ✅ Template error handling verified")
    
    @pytest.mark.integration
    def test_complete_template_workflow(self, temp_workspace, sample_openspec):
        """Test complete template workflow with OpenSpec."""
        print("\n🧪 Testing complete template workflow...")
        
        templates = PromptTemplates()
        
        # Step 1: Generate source code prompt
        interfaces = []
        requirements = []
        
        for req in sample_openspec["requirements"]:
            requirements.append(f"- {req['id']}: {req['description']}")
            for interface in req.get("interfaces", []):
                params = ", ".join([f"{p['name']}: {p['type']}" for p in interface["parameters"]])
                interfaces.append(f"{interface['name']}({params}) -> {interface['return_type']}")
        
        source_prompt = templates.source_code_prompt.format(
            spec_id=sample_openspec["spec_id"],
            interfaces="\n".join(interfaces),
            requirements="\n".join(requirements)
        )
        
        # Step 2: Generate test prompts for each requirement
        test_prompts = []
        for req in sample_openspec["requirements"]:
            test_prompt = templates.test_prompt.format(
                req_id=req["id"],
                req_title=req["title"],
                req_description=req["description"],
                validation=req["validation"]
            )
            test_prompts.append(test_prompt)
        
        # Step 3: Generate documentation prompt
        requirements_text = "\n".join([
            f"- {req['id']}: {req['description']}" 
            for req in sample_openspec["requirements"]
        ])
        
        docs_prompt = templates.documentation_prompt.format(
            spec_id=sample_openspec["spec_id"],
            title=sample_openspec["title"],
            requirements=requirements_text
        )
        
        # Verify workflow completeness
        assert len(source_prompt) > 0
        assert len(test_prompts) == 2  # Two requirements
        assert len(docs_prompt) > 0
        
        # Verify all prompts contain expected content
        assert sample_openspec["spec_id"] in source_prompt
        assert all(req["id"] in prompt for req, prompt in zip(sample_openspec["requirements"], test_prompts))
        assert sample_openspec["spec_id"] in docs_prompt
        
        # Save prompts to files for inspection
        output_dir = temp_workspace / "generated_prompts"
        output_dir.mkdir()
        
        (output_dir / "source_code_prompt.txt").write_text(source_prompt)
        (output_dir / "docs_prompt.txt").write_text(docs_prompt)
        
        for i, test_prompt in enumerate(test_prompts):
            (output_dir / f"test_prompt_{i+1}.txt").write_text(test_prompt)
        
        print(f"   ✅ Complete workflow successful")
        print(f"   📁 Prompts saved to: {output_dir}")
        print(f"   📝 Generated {len(test_prompts)} test prompts")
    
    @pytest.mark.integration
    def test_template_dataclass_properties(self, temp_workspace):
        """Test PromptTemplates dataclass properties."""
        print("\n🧪 Testing PromptTemplates dataclass properties...")
        
        templates = PromptTemplates()
        
        # Test that it's a dataclass
        from dataclasses import is_dataclass
        assert is_dataclass(PromptTemplates)
        
        # Test default values
        assert templates.source_code_prompt != ""
        assert templates.test_prompt != ""
        assert templates.documentation_prompt != ""
        assert templates.system_prompt != ""
        
        # Test field access
        assert hasattr(templates, '__dataclass_fields__')
        field_names = set(templates.__dataclass_fields__.keys())
        expected_fields = {'source_code_prompt', 'test_prompt', 'documentation_prompt', 'system_prompt'}
        assert field_names == expected_fields
        
        print("   ✅ Dataclass properties verified")
    
    @pytest.mark.integration
    def test_template_placeholder_validation(self, temp_workspace):
        """Test template placeholder validation."""
        print("\n🧪 Testing template placeholder validation...")
        
        templates = PromptTemplates()
        
        # Define expected placeholders for each template
        expected_placeholders = {
            'source_code_prompt': {'spec_id', 'interfaces', 'requirements'},
            'test_prompt': {'req_id', 'req_title', 'req_description', 'validation'},
            'documentation_prompt': {'spec_id', 'title', 'requirements'},
            'system_prompt': set()  # No placeholders in system prompt
        }
        
        # Check each template
        for template_name, expected_placeholders_set in expected_placeholders.items():
            template_content = getattr(templates, template_name)
            
            if expected_placeholders_set:
                # Extract placeholders from template content
                import re
                found_placeholders = set(re.findall(r'\{(\w+)\}', template_content))
                
                # Verify all expected placeholders are present
                assert expected_placeholders_set.issubset(found_placeholders), \
                    f"Missing placeholders in {template_name}: {expected_placeholders_set - found_placeholders}"
                
                print(f"   ✅ {template_name}: {len(found_placeholders)} placeholders found")
            else:
                # System prompt should have no placeholders
                import re
                found_placeholders = set(re.findall(r'\{(\w+)\}', template_content))
                assert len(found_placeholders) == 0, f"Unexpected placeholders in system prompt: {found_placeholders}"
                print(f"   ✅ system_prompt: No placeholders (as expected)")
        
        print("   ✅ Template placeholder validation completed")


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "-s"])