"""
OpenSpec Specification Parser

Parses OpenSpec YAML files and extracts requirements, validation criteria,
and metadata for code generation.
"""

import yaml
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class ValidationCriteria:
    """Represents validation criteria for a requirement."""
    type: str  # 'unit', 'integration', etc.
    file: str
    target: str


@dataclass
class FunctionInterface:
    """Represents a function interface specification."""
    function: str
    parameters: Dict[str, str]  # parameter_name: type
    returns: str
    example: Optional[Dict[str, Any]] = None


@dataclass
class Requirement:
    """Represents a single requirement in the specification."""
    id: str
    title: str
    description: str
    interface: Optional[FunctionInterface] = None
    validation: Optional[List[ValidationCriteria]] = None


@dataclass
class OpenSpec:
    """Represents a complete OpenSpec specification."""
    spec_id: str
    title: str
    version: str
    requirements: List[Requirement]
    raw_data: Dict[str, Any]


class SpecParser:
    """Parser for OpenSpec YAML specification files."""
    
    def __init__(self):
        self.specs: Dict[str, OpenSpec] = {}
    
    def parse_file(self, file_path: Path) -> OpenSpec:
        """Parse a single OpenSpec YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return self._parse_data(data, str(file_path))
    
    def parse_string(self, yaml_content: str, source: str = "<string>") -> OpenSpec:
        """Parse OpenSpec YAML from a string."""
        data = yaml.safe_load(yaml_content)
        return self._parse_data(data, source)
    
    def _parse_data(self, data: Dict[str, Any], source: str) -> OpenSpec:
        """Parse raw YAML data into OpenSpec object."""
        # Extract basic metadata
        spec_id = data.get('name', data.get('spec_id', 'unknown'))
        title = data.get('title', data.get('description', 'Untitled Specification'))
        version = data.get('version', '0.1.0')
        
        # Parse requirements
        requirements = []
        for req_data in data.get('requirements', []):
            requirement = self._parse_requirement(req_data)
            requirements.append(requirement)
        
        return OpenSpec(
            spec_id=spec_id,
            title=title,
            version=version,
            requirements=requirements,
            raw_data=data
        )
    
    def _parse_requirement(self, req_data: Dict[str, Any]) -> Requirement:
        """Parse a single requirement from YAML data."""
        req_id = req_data.get('name', req_data.get('id', 'unknown'))
        title = req_data.get('title', req_data.get('name', 'Untitled Requirement'))
        description = req_data.get('description', '')
        
        # Parse interface if present
        interface = None
        if 'interface' in req_data:
            interface_data = req_data['interface']
            interface = FunctionInterface(
                function=interface_data.get('function', ''),
                parameters=interface_data.get('parameters', {}),
                returns=interface_data.get('returns', ''),
                example=interface_data.get('example')
            )
        
        # Parse validation criteria
        validation = []
        validation_data = req_data.get('validation', [])
        
        # Handle both string and list formats for validation
        if isinstance(validation_data, str):
            # Simple string validation
            criteria = ValidationCriteria(
                type='unit',
                file='',
                target=validation_data
            )
            validation.append(criteria)
        elif isinstance(validation_data, list):
            # List of validation criteria
            for val_data in validation_data:
                criteria = ValidationCriteria(
                    type=val_data.get('type', 'unit'),
                    file=val_data.get('file', ''),
                    target=val_data.get('target', 'pass')
                )
                validation.append(criteria)
        
        return Requirement(
            id=req_id,
            title=title,
            description=description,
            interface=interface,
            validation=validation
        )
    
    def format_requirements_for_prompt(self, spec: OpenSpec) -> str:
        """Format requirements for inclusion in AI prompts."""
        formatted = []
        for req in spec.requirements:
            req_text = f"- {req.id}: {req.title}\n"
            req_text += f"  Description: {req.description}\n"
            if req.validation:
                req_text += f"  Validation: {', '.join([f'{v.type} test in {v.file}' for v in req.validation])}\n"
            formatted.append(req_text)
        
        return '\n'.join(formatted)
    
    def format_function_signature(self, requirement: Requirement) -> str:
        """Format a function signature from the requirement interface."""
        if not requirement.interface:
            # Fallback to old format if no interface
            return f"def {requirement.title.lower().replace(' ', '_')}():\n    \"\"\"TODO {requirement.id}: {requirement.description}.\"\"\"\n    pass"
        
        interface = requirement.interface
        
        # Format parameters
        params = []
        for param_name, param_type in interface.parameters.items():
            params.append(f"{param_name}: {param_type}")
        
        param_str = ", ".join(params)
        
        return f"def {interface.function}({param_str}) -> {interface.returns}:\n    \"\"\"TODO {requirement.id}: {requirement.description}.\"\"\"\n    pass"
    
    def format_interfaces_for_prompt(self, spec: OpenSpec) -> str:
        """Format all function interfaces for the AI prompt."""
        formatted = []
        for req in spec.requirements:
            if req.interface:
                formatted.append(f"- {req.interface.function}: {req.description}")
                formatted.append(f"  Parameters: {req.interface.parameters}")
                formatted.append(f"  Returns: {req.interface.returns}")
                if req.interface.example:
                    formatted.append(f"  Example: {req.interface.example}")
                formatted.append("")
        
        return '\n'.join(formatted)
    
    def get_requirement_by_id(self, spec: OpenSpec, req_id: str) -> Optional[Requirement]:
        """Get a specific requirement by its ID."""
        for req in spec.requirements:
            if req.id == req_id:
                return req
        return None
    
    def validate_spec(self, spec: OpenSpec) -> List[str]:
        """Validate the specification and return any issues."""
        issues = []
        
        if not spec.spec_id:
            issues.append("Missing spec_id")
        
        if not spec.title:
            issues.append("Missing title")
        
        if not spec.requirements:
            issues.append("No requirements found")
        
        for i, req in enumerate(spec.requirements):
            if not req.id:
                issues.append(f"Requirement {i+1} missing ID")
            if not req.title:
                issues.append(f"Requirement {i+1} missing title")
            if not req.description:
                issues.append(f"Requirement {i+1} missing description")
        
        return issues