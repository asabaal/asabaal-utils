"""
Comprehensive test suite for the SpecParser class.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from asabaal_utils.agents.spec_coder.spec_parser import SpecParser, OpenSpec, Requirement, FunctionInterface, ValidationCriteria


class TestSpecParser:
    """Test cases for SpecParser class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def parser(self):
        """Create a SpecParser instance."""
        return SpecParser()
    
    @pytest.fixture
    def valid_spec_file(self, temp_dir):
        """Create a valid OpenSpec YAML file."""
        spec_content = {
            'spec_id': 'test-001',
            'title': 'Test Specification',
            'version': '1.0.0',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'Test Requirement 1',
                    'description': 'First test requirement'
                },
                {
                    'id': 'req-002',
                    'title': 'Test Requirement 2',
                    'description': 'Second test requirement'
                }
            ]
        }
        
        spec_file = temp_dir / "valid_spec.yml"
        spec_file.write_text(yaml.dump(spec_content))
        return spec_file
    
    @pytest.fixture
    def invalid_spec_file(self, temp_dir):
        """Create an invalid OpenSpec YAML file."""
        spec_content = {
            'title': 'Invalid Specification',
            # Missing required fields
            'requirements': [
                {
                    'title': 'Invalid Requirement',
                    # Missing id field
                }
            ]
        }
        
        spec_file = temp_dir / "invalid_spec.yml"
        spec_file.write_text(yaml.dump(spec_content))
        return spec_file
    
    def test_parse_file_success(self, parser, valid_spec_file):
        """Test successful parsing of a valid spec file."""
        spec = parser.parse_file(valid_spec_file)
        
        assert isinstance(spec, OpenSpec)
        assert spec.spec_id == 'test-001'
        assert spec.title == 'Test Specification'
        assert spec.version == '1.0.0'
        assert len(spec.requirements) == 2
        
        # Check first requirement
        req1 = spec.requirements[0]
        assert isinstance(req1, Requirement)
        assert req1.id == 'req-001'
        assert req1.title == 'Test Requirement 1'
        assert req1.description == 'First test requirement'
        
        # Check second requirement
        req2 = spec.requirements[1]
        assert req2.id == 'req-002'
    
    def test_parse_file_not_found(self, parser):
        """Test parsing a non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.yml"))
    
    def test_parse_file_invalid_yaml(self, parser, temp_dir):
        """Test parsing an invalid YAML file."""
        invalid_yaml_file = temp_dir / "invalid.yml"
        invalid_yaml_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            parser.parse_file(invalid_yaml_file)
    
    def test_validate_spec_valid(self, parser, valid_spec_file):
        """Test validation of a valid spec."""
        spec = parser.parse_file(valid_spec_file)
        errors = parser.validate_spec(spec)
        
        assert len(errors) == 0
    
    def test_validate_spec_missing_required_fields(self, parser, temp_dir):
        """Test validation of spec with missing required fields."""
        # Create spec with empty spec_id
        spec_content = {
            'spec_id': '',  # Empty spec_id
            'title': 'Incomplete Specification',
            'version': '1.0.0',
            'requirements': []
        }
        
        spec_file = temp_dir / "incomplete_spec.yml"
        spec_file.write_text(yaml.dump(spec_content))
        
        spec = parser.parse_file(spec_file)
        errors = parser.validate_spec(spec)
        
        assert len(errors) > 0
        assert any('spec_id' in error for error in errors)
    
    def test_validate_spec_invalid_requirement(self, parser, temp_dir):
        """Test validation of spec with invalid requirements."""
        spec_content = {
            'spec_id': 'test-002',
            'title': 'Specification with Invalid Requirements',
            'version': '1.0.0',
            'description': 'Test invalid requirements',
            'requirements': [
                {
                    'id': '',  # Empty ID
                    'title': 'Requirement without ID',
                    'description': 'Missing required id field'
                }
            ]
        }
        
        spec_file = temp_dir / "invalid_req_spec.yml"
        spec_file.write_text(yaml.dump(spec_content))
        
        spec = parser.parse_file(spec_file)
        errors = parser.validate_spec(spec)
        
        # The validation does catch empty IDs (even though parser converts them to 'unknown')
        assert len(errors) == 1
        assert 'missing ID' in errors[0]
    
    def test_validate_spec_empty_requirements(self, parser, temp_dir):
        """Test validation of spec with no requirements."""
        spec_content = {
            'spec_id': 'test-003',
            'title': 'Specification without Requirements',
            'version': '1.0.0',
            'description': 'No requirements',
            'requirements': []
        }
        
        spec_file = temp_dir / "no_reqs_spec.yml"
        spec_file.write_text(yaml.dump(spec_content))
        
        spec = parser.parse_file(spec_file)
        errors = parser.validate_spec(spec)
        
        # The parser actually warns about empty requirements
        assert len(errors) == 1
        assert "No requirements found" in errors[0]
    
    def test_requirement_basic_fields(self, parser, temp_dir):
        """Test basic requirement fields."""
        spec_content = {
            'spec_id': 'test-004',
            'title': 'Basic Fields Test',
            'version': '1.0.0',
            'requirements': [
                {
                    'id': 'req-basic',
                    'title': 'Basic Requirement',
                    'description': 'Basic test requirement'
                }
            ]
        }
        
        spec_file = temp_dir / "basic_fields.yml"
        spec_file.write_text(yaml.dump(spec_content))
        
        spec = parser.parse_file(spec_file)
        errors = parser.validate_spec(spec)
        
        assert len(errors) == 0
        assert len(spec.requirements) == 1
        
        # Check basic fields
        req = spec.requirements[0]
        assert req.id == 'req-basic'
        assert req.title == 'Basic Requirement'
        assert req.description == 'Basic test requirement'
    
    def test_format_function_signature_with_interface(self, parser):
        """Test format_function_signature with a proper interface."""
        interface = FunctionInterface(
            function='calculate_sum',
            parameters={'a': 'int', 'b': 'int'},
            returns='int'
        )
        requirement = Requirement(
            id='req-001',
            title='Calculate Sum',
            description='Calculates the sum of two numbers',
            interface=interface
        )
        
        signature = parser.format_function_signature(requirement)
        expected = "def calculate_sum(a: int, b: int) -> int:\n    \"\"\"TODO req-001: Calculates the sum of two numbers.\"\"\"\n    pass"
        assert signature == expected
    
    def test_format_function_signature_without_interface(self, parser):
        """Test format_function_signature without interface (fallback format)."""
        requirement = Requirement(
            id='req-002',
            title='Simple Function',
            description='A simple function without interface'
        )
        
        signature = parser.format_function_signature(requirement)
        expected = "def simple_function():\n    \"\"\"TODO req-002: A simple function without interface.\"\"\"\n    pass"
        assert signature == expected
    
    def test_format_function_signature_empty_interface(self, parser):
        """Test format_function_signature with empty interface."""
        interface = FunctionInterface(
            function='',
            parameters={},
            returns=''
        )
        requirement = Requirement(
            id='req-003',
            title='Empty Interface',
            description='Function with empty interface',
            interface=interface
        )
        
        signature = parser.format_function_signature(requirement)
        expected = "def () -> :\n    \"\"\"TODO req-003: Function with empty interface.\"\"\"\n    pass"
        assert signature == expected
    
    def test_format_requirements_for_prompt(self, parser, temp_dir):
        """Test format_requirements_for_prompt method."""
        spec_content = {
            'spec_id': 'test-005',
            'title': 'Requirements Format Test',
            'version': '1.0.0',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'First Requirement',
                    'description': 'First test requirement',
                    'validation': 'unit test in test_file.py'
                },
                {
                    'id': 'req-002', 
                    'title': 'Second Requirement',
                    'description': 'Second test requirement',
                    'validation': [
                        {'type': 'unit', 'file': 'test1.py', 'target': 'pass'},
                        {'type': 'integration', 'file': 'test2.py', 'target': 'pass'}
                    ]
                }
            ]
        }
        
        spec_file = temp_dir / "format_test.yml"
        spec_file.write_text(yaml.dump(spec_content))
        spec = parser.parse_file(spec_file)
        
        formatted = parser.format_requirements_for_prompt(spec)
        
        assert 'req-001: First Requirement' in formatted
        assert 'Description: First test requirement' in formatted
        assert 'Validation: unit test in ' in formatted
        assert 'req-002: Second Requirement' in formatted
        assert 'unit test in test1.py, integration test in test2.py' in formatted
    
    def test_format_interfaces_for_prompt(self, parser, temp_dir):
        """Test format_interfaces_for_prompt method."""
        spec_content = {
            'spec_id': 'test-006',
            'title': 'Interfaces Format Test',
            'version': '1.0.0',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'Function with Interface',
                    'description': 'A function with interface',
                    'interface': {
                        'function': 'calculate',
                        'parameters': {'x': 'float', 'y': 'float'},
                        'returns': 'float',
                        'example': {'x': 1.0, 'y': 2.0}
                    }
                },
                {
                    'id': 'req-002',
                    'title': 'Function without Interface',
                    'description': 'A function without interface'
                }
            ]
        }
        
        spec_file = temp_dir / "interfaces_test.yml"
        spec_file.write_text(yaml.dump(spec_content))
        spec = parser.parse_file(spec_file)
        
        formatted = parser.format_interfaces_for_prompt(spec)
        
        assert 'calculate: A function with interface' in formatted
        assert 'Parameters: {\'x\': \'float\', \'y\': \'float\'}' in formatted
        assert 'Returns: float' in formatted
        assert 'Example: {\'x\': 1.0, \'y\': 2.0}' in formatted
        # Should not include the requirement without interface
        assert 'Function without Interface' not in formatted
    
    def test_get_requirement_by_id_found(self, parser, temp_dir):
        """Test get_requirement_by_id when requirement exists."""
        spec_content = {
            'spec_id': 'test-007',
            'title': 'Get Requirement Test',
            'version': '1.0.0',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'First Requirement',
                    'description': 'First test requirement'
                },
                {
                    'id': 'req-002',
                    'title': 'Second Requirement', 
                    'description': 'Second test requirement'
                }
            ]
        }
        
        spec_file = temp_dir / "get_req_test.yml"
        spec_file.write_text(yaml.dump(spec_content))
        spec = parser.parse_file(spec_file)
        
        req = parser.get_requirement_by_id(spec, 'req-001')
        assert req is not None
        assert req.id == 'req-001'
        assert req.title == 'First Requirement'
        
        req2 = parser.get_requirement_by_id(spec, 'req-002')
        assert req2 is not None
        assert req2.id == 'req-002'
    
    def test_get_requirement_by_id_not_found(self, parser, temp_dir):
        """Test get_requirement_by_id when requirement doesn't exist."""
        spec_content = {
            'spec_id': 'test-008',
            'title': 'Get Requirement Not Found Test',
            'version': '1.0.0',
            'requirements': [
                {
                    'id': 'req-001',
                    'title': 'Only Requirement',
                    'description': 'Only test requirement'
                }
            ]
        }
        
        spec_file = temp_dir / "get_req_not_found.yml"
        spec_file.write_text(yaml.dump(spec_content))
        spec = parser.parse_file(spec_file)
        
        req = parser.get_requirement_by_id(spec, 'nonexistent')
        assert req is None
    
    def test_parse_string_success(self, parser):
        """Test successful parsing from YAML string."""
        yaml_content = """
spec_id: test-string-001
title: Test String Parsing
version: 1.0.0
requirements:
  - id: req-001
    title: String Requirement
    description: Parsed from string
"""
        
        spec = parser.parse_string(yaml_content, "test_source")
        
        assert isinstance(spec, OpenSpec)
        assert spec.spec_id == 'test-string-001'
        assert spec.title == 'Test String Parsing'
        assert len(spec.requirements) == 1
        assert spec.requirements[0].id == 'req-001'
    
    def test_parse_string_invalid_yaml(self, parser):
        """Test parsing invalid YAML string."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with pytest.raises(yaml.YAMLError):
            parser.parse_string(invalid_yaml)


class TestOpenSpec:
    """Test cases for OpenSpec dataclass."""
    
    def test_open_spec_creation(self):
        """Test OpenSpec creation and attributes."""
        requirements = [
            Requirement(
                id='req-001',
                title='Test Requirement',
                description='A test requirement'
            )
        ]
        
        spec = OpenSpec(
            spec_id='test-001',
            title='Test Spec',
            version='1.0.0',
            requirements=requirements,
            raw_data={}
        )
        
        assert spec.spec_id == 'test-001'
        assert spec.title == 'Test Spec'
        assert spec.version == '1.0.0'
        assert len(spec.requirements) == 1
        assert spec.requirements[0].id == 'req-001'


class TestRequirement:
    """Test cases for Requirement dataclass."""
    
    def test_requirement_creation(self):
        """Test Requirement creation and attributes."""
        req = Requirement(
            id='req-001',
            title='Test Requirement',
            description='A test requirement'
        )
        
        assert req.id == 'req-001'
        assert req.title == 'Test Requirement'
        assert req.description == 'A test requirement'
    
    def test_requirement_optional_fields(self):
        """Test Requirement with optional fields."""
        req = Requirement(
            id='req-002',
            title='Minimal Requirement',
            description='Minimal test requirement'
        )
        
        assert req.id == 'req-002'
        assert req.title == 'Minimal Requirement'
        assert req.description == 'Minimal test requirement'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])