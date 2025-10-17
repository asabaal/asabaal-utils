"""
Comprehensive test suite for the SpecParser class.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from ..spec_parser import SpecParser, OpenSpec, Requirement


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