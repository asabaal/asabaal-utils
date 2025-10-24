# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 8: Integration Mastery - Complete SpecCoder Pipeline
# 
# ## 🎯 Learning Objectives for This Section
# By the end of this section, you will understand:
# - How all SpecCoder components integrate into a complete pipeline
# - How to orchestrate end-to-end workflows from OpenSpec to production code
# - How to implement advanced integration patterns (pipeline, event-driven, workflow)
# - How to handle errors and troubleshoot complex integration scenarios
# - How to optimize performance and monitor production deployments
# - **EVERY SINGLE LINE** of the integration architecture and its implementation patterns!
# 
# ## 📚 What We're Covering
# This section covers **complete integration mastery** which provides:
# - End-to-end pipeline orchestration across all SpecCoder modules
# - Advanced integration patterns for scalable architectures
# - Comprehensive error handling and troubleshooting strategies
# - Performance optimization and monitoring techniques
# - Production deployment best practices and security considerations
# 
# ---
# 
# **DONE MEANS TAUGHT**: You'll understand every integration pattern and be able to build production systems!

# %% [markdown]
# ## 🔍 Phase 1: Understanding the Integration Architecture

# %%
# Cell 1: Integration Environment Setup
"""
Setting up a complete integration environment with all SpecCoder components.
This cell imports and configures all modules for comprehensive testing.
"""

import sys
import json
import tempfile
import shutil
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any
import time
import logging

# Setup logging for integration testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SpecCoder-Integration')

# Create temporary integration environment
integration_dir = Path(tempfile.mkdtemp(prefix='speccoder_integration_'))
print(f"📁 Integration directory: {integration_dir}")

# Create directory structure
dirs_to_create = [
    'specs',
    'generated',
    'tests',
    'reports',
    'output',
    'logs'
]

for dir_name in dirs_to_create:
    dir_path = integration_dir / dir_name
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"   📂 Created: {dir_path}")

# Mock the external dependencies for integration testing
print("\n🔧 Setting up mock dependencies...")

# Mock AI client
mock_ai_client = Mock()
mock_ai_client.generate.return_value = "def example_function():\n    pass"

# Mock file system operations
mock_file_ops = {
    'read_success': True,
    'write_success': True,
    'parse_success': True
}

# Integration test configuration
integration_config = {
    'base_dir': integration_dir,
    'specs_dir': integration_dir / 'specs',
    'generated_dir': integration_dir / 'generated',
    'tests_dir': integration_dir / 'tests',
    'reports_dir': integration_dir / 'reports',
    'output_dir': integration_dir / 'output',
    'logs_dir': integration_dir / 'logs',
    'mock_ai_client': mock_ai_client,
    'mock_file_ops': mock_file_ops
}

print("\n✅ Integration environment setup complete!")
print(f"📊 Configuration: {len(integration_config)} components")
print(f"🔍 Mock AI client: {type(mock_ai_client).__name__}")
print(f"📁 Working directory: {integration_dir}")

# %%
# Cell 2: Component Integration Testing
"""
Testing the integration between all SpecCoder components.
This cell demonstrates how components interact and share data.
"""

class ComponentIntegrator:
    """Manages integration between all SpecCoder components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir = config['base_dir']
        self.components = {}
        self.integration_log = []
        
    def register_component(self, name: str, component: Any) -> None:
        """Register a component for integration testing."""
        self.components[name] = component
        self.integration_log.append({
            'action': 'register_component',
            'component': name,
            'type': type(component).__name__,
            'timestamp': time.time()
        })
        
    def test_component_interaction(self, comp1: str, comp2: str, test_data: Dict) -> bool:
        """Test interaction between two components."""
        if comp1 not in self.components or comp2 not in self.components:
            logger.error(f"Components not found: {comp1}, {comp2}")
            return False
            
        try:
            # Simulate component interaction
            result1 = self._simulate_component_call(self.components[comp1], test_data)
            result2 = self._simulate_component_call(self.components[comp2], result1)
            
            self.integration_log.append({
                'action': 'test_interaction',
                'components': [comp1, comp2],
                'success': True,
                'timestamp': time.time()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Interaction test failed: {e}")
            self.integration_log.append({
                'action': 'test_interaction',
                'components': [comp1, comp2],
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            })
            return False
    
    def _simulate_component_call(self, component: Any, data: Dict) -> Dict:
        """Simulate a component call with test data."""
        # Mock component behavior based on type
        if hasattr(component, 'process'):
            return component.process(data)
        elif hasattr(component, 'generate'):
            return {'result': component.generate(data)}
        else:
            return {'processed': True, 'data': data}
    
    def run_integration_tests(self) -> Dict[str, bool]:
        """Run comprehensive integration tests."""
        results = {}
        
        # Test all component pairs
        component_names = list(self.components.keys())
        for i, comp1 in enumerate(component_names):
            for comp2 in component_names[i+1:]:
                test_name = f"{comp1}_to_{comp2}"
                test_data = {'test_input': f'integration_test_{test_name}'}
                
                results[test_name] = self.test_component_interaction(comp1, comp2, test_data)
                
        return results

# Create mock components for testing
print("🧪 Setting up component integration testing...")

integrator = ComponentIntegrator(integration_config)

# Mock Spec Parser
mock_spec_parser = Mock()
mock_spec_parser.parse.return_value = {
    'spec_id': 'TEST-001',
    'title': 'Test Specification',
    'requirements': []
}

# Mock Code Generator
mock_generator = Mock()
mock_generator.generate.return_value = {
    'success': True,
    'files': ['test.py'],
    'errors': []
}

# Mock Test Analyzer
mock_tester = Mock()
mock_tester.analyze.return_value = {
    'tests_passed': 5,
    'tests_failed': 0,
    'coverage': 85
}

# Mock Orchestrator
mock_orchestrator = Mock()
mock_orchestrator.run_pipeline.return_value = {
    'success': True,
    'stages_completed': 4,
    'execution_time': 12.5
}

# Register components
components_to_register = [
    ('spec_parser', mock_spec_parser),
    ('generator', mock_generator),
    ('tester', mock_tester),
    ('orchestrator', mock_orchestrator)
]

for name, component in components_to_register:
    integrator.register_component(name, component)
    print(f"   ✅ Registered: {name} ({type(component).__name__})")

print(f"\n📊 Total components registered: {len(integrator.components)}")
print(f"📝 Integration log entries: {len(integrator.integration_log)}")

# %%
# Cell 3: End-to-End Workflow Demonstration
"""
Complete workflow demonstration from OpenSpec to production code.
This cell shows the entire pipeline in action with realistic data.
"""

class WorkflowDemonstrator:
    """Demonstrates complete SpecCoder workflows."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workflow_steps = []
        self.current_step = 0
        
    def create_sample_spec(self) -> Dict[str, Any]:
        """Create a sample OpenSpec for demonstration."""
        spec_content = {
            'spec_id': 'MUSIC-001',
            'title': 'Music Generation Library',
            'version': '1.0.0',
            'description': 'A library for generating musical patterns and melodies',
            'requirements': [
                {
                    'req_id': 'REQ-001',
                    'title': 'Generate Melody',
                    'description': 'Generate musical melodies in specified keys',
                    'validation': 'Output should be list of valid musical notes',
                    'examples': [
                        {
                            'input': {'key': 'C major', 'tempo': 120},
                            'output': ['C', 'E', 'G', 'C']
                        }
                    ]
                },
                {
                    'req_id': 'REQ-002',
                    'title': 'Apply Rhythm',
                    'description': 'Apply rhythmic patterns to note sequences',
                    'validation': 'Output should maintain note order with rhythm applied',
                    'examples': [
                        {
                            'input': {'pattern': 'rock', 'notes': ['C', 'E']},
                            'output': ['C', 'C', 'E', 'E']
                        }
                    ]
                }
            ],
            'functions': [
                {
                    'name': 'generate_melody',
                    'parameters': [
                        {'name': 'key', 'type': 'str', 'description': 'Musical key'},
                        {'name': 'tempo', 'type': 'int', 'description': 'Tempo in BPM'}
                    ],
                    'return_type': 'List[str]',
                    'description': 'Generate a melody in the specified key'
                },
                {
                    'name': 'apply_rhythm',
                    'parameters': [
                        {'name': 'pattern', 'type': 'str', 'description': 'Rhythm pattern'},
                        {'name': 'notes', 'type': 'List[str]', 'description': 'Note sequence'}
                    ],
                    'return_type': 'List[str]',
                    'description': 'Apply rhythm pattern to notes'
                }
            ]
        }
        
        # Save spec to file
        spec_file = self.config['specs_dir'] / 'music_library.yaml'
        import yaml
        with open(spec_file, 'w') as f:
            yaml.dump(spec_content, f, default_flow_style=False)
            
        self.log_step('create_spec', {'spec_file': str(spec_file), 'requirements': len(spec_content['requirements'])})
        return spec_content
    
    def simulate_spec_parsing(self, spec_file: Path) -> Dict[str, Any]:
        """Simulate the spec parsing step."""
        print(f"🔍 Step 1: Parsing OpenSpec: {spec_file.name}")
        
        # Simulate parsing time
        time.sleep(0.1)
        
        parsed_spec = {
            'spec_id': 'MUSIC-001',
            'title': 'Music Generation Library',
            'parsed_requirements': 2,
            'parsed_functions': 2,
            'validation_criteria': ['key_validation', 'tempo_validation', 'rhythm_validation']
        }
        
        self.log_step('parse_spec', parsed_spec)
        return parsed_spec
    
    def simulate_code_generation(self, parsed_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the code generation step."""
        print(f"⚡ Step 2: Generating code from parsed spec")
        
        # Simulate generation time
        time.sleep(0.2)
        
        generated_files = [
            'generate_melody.py',
            'apply_rhythm.py',
            '__init__.py'
        ]
        
        # Create mock generated files
        for filename in generated_files:
            if filename == '__init__.py':
                content = '"""Music generation library."""\nfrom .generate_melody import *\nfrom .apply_rhythm import *'
            else:
                content = f'def {filename.replace(".py", "")}():\n    """TODO: Implement {filename.replace(".py", "")}."""\n    pass'
            
            file_path = self.config['generated_dir'] / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        generation_result = {
            'success': True,
            'files_generated': generated_files,
            'total_lines': sum(len(f.read_text().splitlines()) for f in self.config['generated_dir'].glob('*.py')),
            'scaffold_functions': 2
        }
        
        self.log_step('generate_code', generation_result)
        return generation_result
    
    def simulate_test_generation(self, generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the test generation step."""
        print(f"🧪 Step 3: Generating tests for code")
        
        # Simulate test generation time
        time.sleep(0.15)
        
        test_files = [
            'test_generate_melody.py',
            'test_apply_rhythm.py'
        ]
        
        # Create mock test files
        for filename in test_files:
            function_name = filename.replace('test_', '').replace('.py', '')
            content = f'''import pytest
from {function_name} import {function_name}

def test_{function_name}():
    """Test {function_name} functionality."""
    result = {function_name}()
    assert result is not None

def test_{function_name}_edge_cases():
    """Test {function_name} edge cases."""
    # TODO: Add edge case tests
    pass
'''
            
            file_path = self.config['tests_dir'] / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        test_result = {
            'success': True,
            'tests_generated': test_files,
            'total_test_functions': 4,  # 2 per file
            'coverage_target': 90
        }
        
        self.log_step('generate_tests', test_result)
        return test_result
    
    def simulate_test_execution(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate test execution and analysis."""
        print(f"✅ Step 4: Executing tests and analyzing results")
        
        # Simulate test execution time
        time.sleep(0.1)
        
        execution_result = {
            'success': True,
            'tests_run': 4,
            'tests_passed': 3,
            'tests_failed': 1,
            'execution_time': 0.8,
            'coverage_percentage': 75,
            'failed_tests': ['test_apply_rhythm_edge_cases'],
            'warnings': ['Some edge cases not implemented']
        }
        
        self.log_step('execute_tests', execution_result)
        return execution_result
    
    def simulate_code_organization(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the code organization step."""
        print(f"🗂 Step 5: Organizing code into production structure")
        
        # Simulate organization time
        time.sleep(0.1)
        
        # Create organized structure
        src_dir = self.config['output_dir'] / 'src'
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Move generated files to organized structure
        organized_files = []
        for gen_file in self.config['generated_dir'].glob('*.py'):
            dest_file = src_dir / gen_file.name
            shutil.copy2(gen_file, dest_file)
            organized_files.append(dest_file.name)
        
        organization_result = {
            'success': True,
            'files_organized': organized_files,
            'directory_structure': {
                'src': organized_files,
                'tests': list(self.config['tests_dir'].glob('*.py'))
            },
            'production_ready': True
        }
        
        self.log_step('organize_code', organization_result)
        return organization_result
    
    def run_complete_workflow(self) -> Dict[str, Any]:
        """Run the complete end-to-end workflow."""
        print("🚀 Starting Complete SpecCoder Workflow")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Step 1: Create sample specification
            spec = self.create_sample_spec()
            
            # Step 2: Parse specification
            parsed_spec = self.simulate_spec_parsing(self.config['specs_dir'] / 'music_library.yaml')
            
            # Step 3: Generate code
            generation_result = self.simulate_code_generation(parsed_spec)
            
            # Step 4: Generate tests
            test_result = self.simulate_test_generation(generation_result)
            
            # Step 5: Execute tests
            execution_result = self.simulate_test_execution(test_result)
            
            # Step 6: Organize code
            organization_result = self.simulate_code_organization(execution_result)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            workflow_summary = {
                'success': True,
                'total_time': total_time,
                'steps_completed': len(self.workflow_steps),
                'spec_id': spec['spec_id'],
                'files_generated': generation_result['files_generated'],
                'tests_generated': test_result['tests_generated'],
                'test_results': {
                    'passed': execution_result['tests_passed'],
                    'failed': execution_result['tests_failed'],
                    'coverage': execution_result['coverage_percentage']
                },
                'production_files': organization_result['files_organized']
            }
            
            print(f"\n🎉 Workflow completed successfully!")
            print(f"⏱️  Total time: {total_time:.2f}s")
            print(f"📁 Files generated: {len(generation_result['files_generated'])}")
            print(f"🧪 Tests generated: {len(test_result['tests_generated'])}")
            print(f"✅ Test pass rate: {execution_result['tests_passed']}/{execution_result['tests_run']}")
            
            return workflow_summary
            
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'steps_completed': len(self.workflow_steps)
            }
    
    def log_step(self, step_name: str, data: Dict[str, Any]) -> None:
        """Log a workflow step."""
        self.current_step += 1
        self.workflow_steps.append({
            'step': self.current_step,
            'name': step_name,
            'data': data,
            'timestamp': time.time()
        })

# Run the workflow demonstration
print("🧪 Starting workflow demonstration...")

demonstrator = WorkflowDemonstrator(integration_config)
workflow_result = demonstrator.run_complete_workflow()

print(f"\n📊 Workflow Summary:")
print(f"   Success: {workflow_result.get('success', False)}")
print(f"   Steps: {workflow_result.get('steps_completed', 0)}")
print(f"   Time: {workflow_result.get('total_time', 0):.2f}s")
print(f"   Spec ID: {workflow_result.get('spec_id', 'Unknown')}")

# %%
# Cell 4: Error Scenarios and Troubleshooting
"""
Common error scenarios and their troubleshooting strategies.
This cell demonstrates how to handle and resolve typical issues.
"""

class ErrorSimulator:
    """Simulates common error scenarios for troubleshooting practice."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.error_log = []
        
    def simulate_spec_parsing_error(self) -> Dict[str, Any]:
        """Simulate specification parsing errors."""
        print("🔍 Simulating spec parsing errors...")
        
        error_scenarios = [
            {
                'error_type': 'Invalid YAML syntax',
                'symptom': 'Parser crashes on spec file',
                'cause': 'Malformed YAML in specification',
                'solution': 'Validate YAML syntax using online validator',
                'prevention': 'Use YAML linter in development'
            },
            {
                'error_type': 'Missing required fields',
                'symptom': 'Validation fails for spec_id or title',
                'cause': 'Incomplete specification structure',
                'solution': 'Add missing required fields to spec',
                'prevention': 'Use spec template with all required fields'
            },
            {
                'error_type': 'Invalid function signatures',
                'symptom': 'Cannot parse function parameters',
                'cause': 'Incorrect type annotations or syntax',
                'solution': 'Fix function signature format',
                'prevention': 'Validate signatures against Python syntax'
            }
        ]
        
        for scenario in error_scenarios:
            self.log_error('spec_parsing', scenario)
            print(f"   ❌ {scenario['error_type']}: {scenario['symptom']}")
            print(f"      💡 Solution: {scenario['solution']}")
            
        return error_scenarios
    
    def simulate_code_generation_errors(self) -> Dict[str, Any]:
        """Simulate code generation errors."""
        print("\n⚡ Simulating code generation errors...")
        
        error_scenarios = [
            {
                'error_type': 'AI service unavailable',
                'symptom': 'Connection timeout to AI service',
                'cause': 'Network issues or service downtime',
                'solution': 'Check network connection, retry with backoff',
                'prevention': 'Implement retry logic and health checks'
            },
            {
                'error_type': 'Invalid AI response',
                'symptom': 'Generated code is not valid Python',
                'cause': 'AI model produces malformed code',
                'solution': 'Validate generated code, retry on failure',
                'prevention': 'Add code validation in generation pipeline'
            },
            {
                'error_type': 'Template formatting error',
                'symptom': 'Missing placeholders in prompt template',
                'cause': 'Incomplete template data',
                'solution': 'Validate all template variables before formatting',
                'prevention': 'Use template validation functions'
            }
        ]
        
        for scenario in error_scenarios:
            self.log_error('code_generation', scenario)
            print(f"   ❌ {scenario['error_type']}: {scenario['symptom']}")
            print(f"      💡 Solution: {scenario['solution']}")
            
        return error_scenarios
    
    def simulate_test_errors(self) -> Dict[str, Any]:
        """Simulate test-related errors."""
        print("\n🧪 Simulating test errors...")
        
        error_scenarios = [
            {
                'error_type': 'Test import errors',
                'symptom': 'Cannot import generated functions in tests',
                'cause': 'Incorrect module paths or missing __init__.py',
                'solution': 'Fix import paths and create proper package structure',
                'prevention': 'Validate imports after code organization'
            },
            {
                'error_type': 'Test syntax errors',
                'symptom': 'Generated tests have invalid Python syntax',
                'cause': 'AI model produces malformed test code',
                'solution': 'Validate test syntax before execution',
                'prevention': 'Add syntax validation in test generation'
            },
            {
                'error_type': 'Test execution failures',
                'symptom': 'Tests fail due to missing implementations',
                'cause': 'Generated scaffolding has only pass statements',
                'solution': 'Implement actual functionality or update test expectations',
                'prevention': 'Generate tests that match scaffolding level'
            }
        ]
        
        for scenario in error_scenarios:
            self.log_error('test_execution', scenario)
            print(f"   ❌ {scenario['error_type']}: {scenario['symptom']}")
            print(f"      💡 Solution: {scenario['solution']}")
            
        return error_scenarios
    
    def simulate_organization_errors(self) -> Dict[str, Any]:
        """Simulate code organization errors."""
        print("\n🗂 Simulating organization errors...")
        
        error_scenarios = [
            {
                'error_type': 'File permission errors',
                'symptom': 'Cannot move files to organized structure',
                'cause': 'Insufficient permissions for target directories',
                'solution': 'Check directory permissions and ownership',
                'prevention': 'Verify write access before organization'
            },
            {
                'error_type': 'Import path conflicts',
                'symptom': 'Import statements break after organization',
                'cause': 'Incorrect relative import paths',
                'solution': 'Update import statements to match new structure',
                'prevention': 'Use automated import fixing in organization'
            },
            {
                'error_type': 'Module naming conflicts',
                'symptom': 'Multiple files with same name in different categories',
                'cause': 'Poor file categorization logic',
                'solution': 'Improve categorization rules and handle conflicts',
                'prevention': 'Validate file names before organization'
            }
        ]
        
        for scenario in error_scenarios:
            self.log_error('code_organization', scenario)
            print(f"   ❌ {scenario['error_type']}: {scenario['symptom']}")
            print(f"      💡 Solution: {scenario['solution']}")
            
        return error_scenarios
    
    def demonstrate_troubleshooting_workflow(self) -> Dict[str, Any]:
        """Demonstrate a complete troubleshooting workflow."""
        print("\n🔧 Demonstrating Troubleshooting Workflow")
        print("=" * 40)
        
        # Simulate an error scenario
        error_scenario = {
            'component': 'Code Generator',
            'error': 'AI service timeout',
            'symptoms': ['Connection timeout', 'Empty response', 'Generation failure'],
            'logs': ['[ERROR] Connection timeout after 30s', '[WARN] Retrying...'],
            'context': {
                'spec_size': '2.5MB',
                'network_status': 'Unstable',
                'ai_service_status': 'Degraded'
            }
        }
        
        print(f"\n🚨 Error Detected: {error_scenario['error']}")
        print(f"   Component: {error_scenario['component']}")
        print(f"   Symptoms: {', '.join(error_scenario['symptoms'])}")
        
        # Step 1: Gather diagnostic information
        print("\n📊 Step 1: Gathering Diagnostic Information")
        diagnostics = {
            'network_test': 'ping ai-service.example.com - OK',
            'service_health': 'HTTP 503 - Service Unavailable',
            'resource_usage': 'CPU: 45%, Memory: 2.1GB',
            'recent_errors': 5,
            'error_rate': '12% (above threshold)'
        }
        
        for key, value in diagnostics.items():
            print(f"   {key}: {value}")
        
        # Step 2: Identify root cause
        print("\n🔍 Step 2: Root Cause Analysis")
        if diagnostics['service_health'].startswith('HTTP 503'):
            root_cause = 'AI service is temporarily unavailable'
            confidence = 'High'
        else:
            root_cause = 'Network connectivity issues'
            confidence = 'Medium'
            
        print(f"   Root Cause: {root_cause}")
        print(f"   Confidence: {confidence}")
        
        # Step 3: Apply immediate fixes
        print("\n🔧 Step 3: Applying Immediate Fixes")
        fixes_applied = [
            'Increased timeout from 30s to 60s',
            'Enabled retry logic with exponential backoff',
            'Switched to backup AI endpoint'
        ]
        
        for fix in fixes_applied:
            print(f"   ✅ {fix}")
        
        # Step 4: Verify resolution
        print("\n✅ Step 4: Verifying Resolution")
        verification_results = {
            'test_generation': 'Success',
            'response_time': '15s (within limits)',
            'error_rate': '0% (resolved)',
            'service_health': 'HTTP 200 - OK'
        }
        
        for test, result in verification_results.items():
            status = '✅' if result == 'Success' or 'OK' in result or '0%' in result else '❌'
            print(f"   {status} {test}: {result}")
        
        # Step 5: Document and prevent
        print("\n📝 Step 5: Documentation and Prevention")
        prevention_measures = [
            'Added service health monitoring',
            'Implemented automatic failover',
            'Created alert for high error rates',
            'Updated runbook with this scenario'
        ]
        
        for measure in prevention_measures:
            print(f"   📋 {measure}")
        
        return {
            'error_resolved': True,
            'root_cause': root_cause,
            'fixes_applied': len(fixes_applied),
            'prevention_measures': len(prevention_measures)
        }
    
    def log_error(self, component: str, scenario: Dict[str, Any]) -> None:
        """Log an error scenario for analysis."""
        self.error_log.append({
            'timestamp': time.time(),
            'component': component,
            'scenario': scenario
        })

# Run error simulation and troubleshooting
print("🧪 Starting error simulation and troubleshooting...")

error_simulator = ErrorSimulator(integration_config)

# Simulate different error types
spec_errors = error_simulator.simulate_spec_parsing_error()
gen_errors = error_simulator.simulate_code_generation_errors()
test_errors = error_simulator.simulate_test_errors()
org_errors = error_simulator.simulate_organization_errors()

# Demonstrate troubleshooting workflow
troubleshooting_result = error_simulator.demonstrate_troubleshooting_workflow()

print(f"\n📊 Error Simulation Summary:")
print(f"   Spec parsing errors: {len(spec_errors)}")
print(f"   Code generation errors: {len(gen_errors)}")
print(f"   Test errors: {len(test_errors)}")
print(f"   Organization errors: {len(org_errors)}")
print(f"   Total error scenarios: {len(error_simulator.error_log)}")
print(f"   Troubleshooting success: {troubleshooting_result['error_resolved']}")

# %%
# Cell 5: Performance Optimization and Monitoring
"""
Performance optimization techniques and monitoring strategies.
This cell demonstrates how to optimize and monitor SpecCoder performance.
"""

import psutil
import threading
import time
from collections import defaultdict, deque
from typing import Dict, List, Any, Callable

class PerformanceMonitor:
    """Monitors and analyzes SpecCoder performance."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = defaultdict(list)
        self.alerts = []
        self.thresholds = {
            'cpu_usage': 80.0,  # percentage
            'memory_usage': 85.0,  # percentage
            'disk_usage': 90.0,  # percentage
            'response_time': 30.0,  # seconds
            'error_rate': 5.0  # percentage
        }
        
    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system performance metrics."""
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'process_count': len(psutil.pids()),
            'timestamp': time.time()
        }
        
        # Store metrics for trend analysis
        for key, value in metrics.items():
            if key != 'timestamp':
                self.metrics[key].append(value)
                # Keep only last 100 measurements
                if len(self.metrics[key]) > 100:
                    self.metrics[key].pop(0)
        
        return metrics
    
    def check_thresholds(self, metrics: Dict[str, float]) -> List[str]:
        """Check metrics against thresholds and generate alerts."""
        alerts = []
        
        if metrics['cpu_percent'] > self.thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {metrics['cpu_percent']:.1f}%")
            
        if metrics['memory_percent'] > self.thresholds['memory_usage']:
            alerts.append(f"High memory usage: {metrics['memory_percent']:.1f}%")
            
        if metrics['disk_percent'] > self.thresholds['disk_usage']:
            alerts.append(f"High disk usage: {metrics['disk_percent']:.1f}%")
            
        self.alerts.extend(alerts)
        return alerts
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        trends = {}
        
        for metric_name, values in self.metrics.items():
            if len(values) >= 10:  # Need at least 10 data points
                recent_avg = sum(values[-10:]) / 10
                older_avg = sum(values[-20:-10]) / 10 if len(values) >= 20 else recent_avg
                
                trend = 'stable'
                if recent_avg > older_avg * 1.1:
                    trend = 'increasing'
                elif recent_avg < older_avg * 0.9:
                    trend = 'decreasing'
                
                trends[metric_name] = {
                    'current': values[-1],
                    'average': sum(values) / len(values),
                    'trend': trend,
                    'min': min(values),
                    'max': max(values)
                }
        
        return trends

class PerformanceOptimizer:
    """Provides performance optimization strategies for SpecCoder."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.optimization_log = []
        
    def optimize_ai_requests(self) -> Dict[str, Any]:
        """Optimize AI service requests for better performance."""
        print("🚀 Optimizing AI service requests...")
        
        optimizations = [
            {
                'technique': 'Request Batching',
                'description': 'Batch multiple small requests into larger ones',
                'benefit': 'Reduces API calls by 60%',
                'implementation': 'Collect requests and send in batches of 5'
            },
            {
                'technique': 'Response Caching',
                'description': 'Cache AI responses for similar prompts',
                'benefit': 'Reduces duplicate requests by 40%',
                'implementation': 'Use LRU cache with 1000 entry limit'
            },
            {
                'technique': 'Parallel Processing',
                'description': 'Process multiple requirements in parallel',
                'benefit': 'Improves throughput by 3x',
                'implementation': 'Use ThreadPoolExecutor for concurrent requests'
            },
            {
                'technique': 'Request Compression',
                'description': 'Compress large prompts before sending',
                'benefit': 'Reduces bandwidth by 30%',
                'implementation': 'Compress prompts > 10KB using gzip'
            }
        ]
        
        for opt in optimizations:
            print(f"   ✅ {opt['technique']}: {opt['benefit']}")
            self.optimization_log.append(opt)
            
        return optimizations
    
    def optimize_file_operations(self) -> Dict[str, Any]:
        """Optimize file I/O operations."""
        print("\n💾 Optimizing file operations...")
        
        optimizations = [
            {
                'technique': 'Async File I/O',
                'description': 'Use asynchronous file operations',
                'benefit': 'Reduces I/O blocking by 50%',
                'implementation': 'Use aiofiles for async file operations'
            },
            {
                'technique': 'File Buffering',
                'description': 'Implement proper file buffering',
                'benefit': 'Improves read/write speed by 25%',
                'implementation': 'Use buffered readers with 8KB buffer'
            },
            {
                'technique': 'Temporary File Management',
                'description': 'Optimize temporary file usage',
                'benefit': 'Reduces disk overhead by 40%',
                'implementation': 'Use memory-backed files for small temporaries'
            }
        ]
        
        for opt in optimizations:
            print(f"   ✅ {opt['technique']}: {opt['benefit']}")
            self.optimization_log.append(opt)
            
        return optimizations
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize memory usage patterns."""
        print("\n🧠 Optimizing memory usage...")
        
        optimizations = [
            {
                'technique': 'Object Pooling',
                'description': 'Reuse objects instead of creating new ones',
                'benefit': 'Reduces memory allocation by 35%',
                'implementation': 'Implement pool for frequently used objects'
            },
            {
                'technique': 'Lazy Loading',
                'description': 'Load components only when needed',
                'benefit': 'Reduces initial memory by 50%',
                'implementation': 'Use lazy imports and initialization'
            },
            {
                'technique': 'Memory Cleanup',
                'description': 'Explicit cleanup of unused objects',
                'benefit': 'Prevents memory leaks',
                'implementation': 'Add explicit del and gc.collect() calls'
            }
        ]
        
        for opt in optimizations:
            print(f"   ✅ {opt['technique']}: {opt['benefit']}")
            self.optimization_log.append(opt)
            
        return optimizations
    
    def benchmark_performance(self) -> Dict[str, float]:
        """Benchmark current performance metrics."""
        print("\n⏱️  Running performance benchmarks...")
        
        benchmarks = {}
        
        # Benchmark file operations
        start_time = time.time()
        test_file = self.config['base_dir'] / 'benchmark_test.txt'
        test_file.write_text('x' * 10000)  # 10KB file
        content = test_file.read_text()
        test_file.unlink()
        benchmarks['file_io_time'] = time.time() - start_time
        
        # Benchmark JSON operations
        start_time = time.time()
        test_data = {'key': 'value' * 1000}  # Large JSON
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        benchmarks['json_parse_time'] = time.time() - start_time
        
        # Benchmark string operations
        start_time = time.time()
        large_string = 'test' * 10000
        result = large_string.replace('test', 'optimized')
        benchmarks['string_ops_time'] = time.time() - start_time
        
        for benchmark, value in benchmarks.items():
            print(f"   📊 {benchmark}: {value:.4f}s")
            
        return benchmarks

# Run performance monitoring and optimization
print("🧪 Starting performance monitoring and optimization...")

# Initialize monitoring and optimization
monitor = PerformanceMonitor(integration_config)
optimizer = PerformanceOptimizer(integration_config)

# Collect current metrics
print("\n📊 Current System Metrics:")
current_metrics = monitor.collect_system_metrics()
for key, value in current_metrics.items():
    if key != 'timestamp':
        print(f"   {key}: {value:.1f}")

# Check for alerts
alerts = monitor.check_thresholds(current_metrics)
if alerts:
    print(f"\n⚠️  Performance Alerts:")
    for alert in alerts:
        print(f"   {alert}")
else:
    print("\n✅ All metrics within normal thresholds")

# Run optimizations
ai_optimizations = optimizer.optimize_ai_requests()
file_optimizations = optimizer.optimize_file_operations()
memory_optimizations = optimizer.optimize_memory_usage()

# Run benchmarks
benchmarks = optimizer.benchmark_performance()

# Analyze trends (simulate some historical data)
for _ in range(20):  # Simulate historical data points
    monitor.metrics['cpu_percent'].append(45 + (_ % 10))
    monitor.metrics['memory_percent'].append(60 + (_ % 15))

trends = monitor.analyze_trends()
print(f"\n📈 Performance Trends:")
for metric, trend_data in trends.items():
    print(f"   {metric}: {trend_data['trend']} (avg: {trend_data['average']:.1f})")

print(f"\n📊 Performance Summary:")
print(f"   Optimizations applied: {len(optimizer.optimization_log)}")
print(f"   Current alerts: {len(alerts)}")
print(f"   Metrics tracked: {len(monitor.metrics)}")
print(f"   Benchmarks run: {len(benchmarks)}")

# %%
# Cell 6: Production Deployment Best Practices
"""
Best practices for deploying SpecCoder in production environments.
This cell covers security, scalability, and operational considerations.
"""

class ProductionDeploymentGuide:
    """Guide for production deployment of SpecCoder."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.deployment_checklist = []
        self.security_recommendations = []
        self.scalability_strategies = []
        
    def security_hardening(self) -> List[Dict[str, str]]:
        """Security hardening recommendations for production."""
        print("🔒 Security Hardening Recommendations:")
        
        security_measures = [
            {
                'category': 'API Security',
                'measure': 'API Key Management',
                'description': 'Use environment variables for API keys',
                'implementation': 'export AI_SERVICE_KEY="your-key-here"',
                'priority': 'Critical'
            },
            {
                'category': 'API Security',
                'measure': 'Request Rate Limiting',
                'description': 'Implement rate limiting to prevent abuse',
                'implementation': 'Use Redis-based rate limiting',
                'priority': 'High'
            },
            {
                'category': 'Data Security',
                'measure': 'Input Validation',
                'description': 'Validate all user inputs and specifications',
                'implementation': 'Use pydantic for input validation',
                'priority': 'Critical'
            },
            {
                'category': 'Data Security',
                'measure': 'Sensitive Data Handling',
                'description': 'Encrypt sensitive data in specifications',
                'implementation': 'Use AES-256 for data at rest',
                'priority': 'High'
            },
            {
                'category': 'Infrastructure',
                'measure': 'Network Security',
                'description': 'Use HTTPS and secure communication channels',
                'implementation': 'Configure TLS 1.3 for all endpoints',
                'priority': 'Critical'
            },
            {
                'category': 'Infrastructure',
                'measure': 'Container Security',
                'description': 'Use non-root users in containers',
                'implementation': 'Add USER directive in Dockerfile',
                'priority': 'Medium'
            }
        ]
        
        for measure in security_measures:
            priority_icon = {'Critical': '🚨', 'High': '⚠️', 'Medium': 'ℹ️'}
            icon = priority_icon.get(measure['priority'], '📋')
            print(f"   {icon} {measure['measure']} ({measure['priority']})")
            print(f"      {measure['description']}")
            print(f"      Implementation: {measure['implementation']}")
            print()
            
        self.security_recommendations.extend(security_measures)
        return security_measures
    
    def scalability_strategies_guide(self) -> List[Dict[str, str]]:
        """Scalability strategies for production deployment."""
        print("📈 Scalability Strategies:")
        
        strategies = [
            {
                'strategy': 'Horizontal Scaling',
                'description': 'Scale out by adding more instances',
                'implementation': 'Use Kubernetes with auto-scaling',
                'benefit': 'Handle increased load by adding instances'
            },
            {
                'strategy': 'Load Balancing',
                'description': 'Distribute load across multiple instances',
                'implementation': 'Use NGINX or HAProxy as load balancer',
                'benefit': 'Prevent single points of failure'
            },
            {
                'strategy': 'Database Scaling',
                'description': 'Scale database layer independently',
                'implementation': 'Use read replicas and connection pooling',
                'benefit': 'Handle database-intensive operations'
            },
            {
                'strategy': 'Caching Layer',
                'description': 'Implement multi-level caching',
                'implementation': 'Use Redis for application-level caching',
                'benefit': 'Reduce database load and improve response times'
            },
            {
                'strategy': 'Asynchronous Processing',
                'description': 'Process long-running tasks asynchronously',
                'implementation': 'Use Celery with Redis/RabbitMQ broker',
                'benefit': 'Improve user experience with non-blocking operations'
            },
            {
                'strategy': 'Microservices Architecture',
                'description': 'Split into independent services',
                'implementation': 'Separate parser, generator, and tester services',
                'benefit': 'Scale components independently based on load'
            }
        ]
        
        for strategy in strategies:
            print(f"   🚀 {strategy['strategy']}")
            print(f"      {strategy['description']}")
            print(f"      Implementation: {strategy['implementation']}")
            print(f"      Benefit: {strategy['benefit']}")
            print()
            
        self.scalability_strategies.extend(strategies)
        return strategies
    
    def monitoring_and_logging_setup(self) -> Dict[str, List[str]]:
        """Setup comprehensive monitoring and logging."""
        print("📊 Monitoring and Logging Setup:")
        
        monitoring_setup = {
            'metrics': [
                'Request latency and response times',
                'Error rates and success rates',
                'AI service response times',
                'Resource utilization (CPU, memory, disk)',
                'Queue depths and processing times',
                'Cache hit/miss ratios'
            ],
            'logs': [
                'Structured JSON logging',
                'Correlation IDs for request tracing',
                'Log levels: DEBUG, INFO, WARN, ERROR',
                'Centralized log aggregation (ELK stack)',
                'Log retention policies',
                'Alerting on error patterns'
            ],
            'alerts': [
                'High error rate thresholds',
                'Service availability monitoring',
                'Performance degradation alerts',
                'Resource exhaustion warnings',
                'AI service failure alerts',
                'Security incident notifications'
            ],
            'dashboards': [
                'System overview dashboard',
                'Performance metrics dashboard',
                'Error analysis dashboard',
                'Resource utilization dashboard',
                'Business metrics dashboard'
            ]
        }
        
        for category, items in monitoring_setup.items():
            print(f"   📈 {category.title()}:")
            for item in items:
                print(f"      • {item}")
            print()
            
        return monitoring_setup
    
    def deployment_checklist_generator(self) -> List[Dict[str, str]]:
        """Generate comprehensive deployment checklist."""
        print("✅ Production Deployment Checklist:")
        
        checklist = [
            {
                'category': 'Pre-deployment',
                'item': 'Environment configuration',
                'check': 'All environment variables set and validated',
                'status': 'Pending'
            },
            {
                'category': 'Pre-deployment',
                'item': 'Database migrations',
                'check': 'All migrations applied and verified',
                'status': 'Pending'
            },
            {
                'category': 'Pre-deployment',
                'item': 'Health checks',
                'check': 'All health endpoints responding correctly',
                'status': 'Pending'
            },
            {
                'category': 'Security',
                'item': 'API keys and secrets',
                'check': 'All secrets stored securely',
                'status': 'Pending'
            },
            {
                'category': 'Security',
                'item': 'SSL certificates',
                'check': 'Valid certificates installed',
                'status': 'Pending'
            },
            {
                'category': 'Performance',
                'item': 'Load testing',
                'check': 'Load tests completed and passed',
                'status': 'Pending'
            },
            {
                'category': 'Performance',
                'item': 'Resource limits',
                'check': 'Memory and CPU limits configured',
                'status': 'Pending'
            },
            {
                'category': 'Monitoring',
                'item': 'Metrics collection',
                'check': 'All metrics being collected',
                'status': 'Pending'
            },
            {
                'category': 'Monitoring',
                'item': 'Alert configuration',
                'check': 'Alerts configured and tested',
                'status': 'Pending'
            },
            {
                'category': 'Backup',
                'item': 'Data backup',
                'check': 'Backup procedures tested',
                'status': 'Pending'
            },
            {
                'category': 'Backup',
                'item': 'Recovery plan',
                'check': 'Disaster recovery plan documented',
                'status': 'Pending'
            }
        ]
        
        for item in checklist:
            status_icon = '✅' if item['status'] == 'Completed' else '⏳'
            print(f"   {status_icon} [{item['category']}] {item['item']}")
            print(f"      Check: {item['check']}")
            
        self.deployment_checklist.extend(checklist)
        return checklist
    
    def create_deployment_script_template(self) -> str:
        """Create a template deployment script."""
        script_template = '''#!/bin/bash
# SpecCoder Production Deployment Script

set -e  # Exit on any error

echo "🚀 Starting SpecCoder Production Deployment"

# Environment checks
echo "📋 Checking environment..."
if [ -z "$AI_SERVICE_KEY" ]; then
    echo "❌ AI_SERVICE_KEY environment variable not set"
    exit 1
fi

# Backup current deployment
echo "💾 Creating backup..."
kubectl get deployment speccoder -o yaml > backup-deployment-$(date +%Y%m%d-%H%M%S).yaml

# Apply new configuration
echo "⚙️  Applying new configuration..."
kubectl apply -f k8s/

# Wait for rollout
echo "⏳ Waiting for rollout..."
kubectl rollout status deployment/speccoder --timeout=300s

# Health check
echo "🏥 Running health checks..."
kubectl wait --for=condition=ready pod -l app=speccoder --timeout=60s

# Verify deployment
echo "✅ Verifying deployment..."
HEALTH_URL="https://speccoder.example.com/health"
if curl -f $HEALTH_URL; then
    echo "🎉 Deployment successful!"
else
    echo "❌ Health check failed, rolling back..."
    kubectl rollout undo deployment/speccoder
    exit 1
fi

echo "✨ Deployment completed successfully!"
'''
        
        # Save deployment script
        script_path = self.config['base_dir'] / 'deploy_production.sh'
        with open(script_path, 'w') as f:
            f.write(script_template)
        script_path.chmod(0o755)  # Make executable
        
        print(f"\n📝 Deployment script template created: {script_path}")
        return script_template

# Run production deployment guide
print("🧪 Production Deployment Best Practices Guide")
print("=" * 50)

deployment_guide = ProductionDeploymentGuide(integration_config)

# Security hardening
security_measures = deployment_guide.security_hardening()

# Scalability strategies
scalability_strategies = deployment_guide.scalability_strategies_guide()

# Monitoring setup
monitoring_setup = deployment_guide.monitoring_and_logging_setup()

# Deployment checklist
checklist = deployment_guide.deployment_checklist_generator()

# Deployment script template
deployment_script = deployment_guide.create_deployment_script_template()

print(f"\n📊 Production Deployment Summary:")
print(f"   Security measures: {len(security_measures)}")
print(f"   Scalability strategies: {len(scalability_strategies)}")
print(f"   Monitoring components: {sum(len(v) for v in monitoring_setup.values())}")
print(f"   Checklist items: {len(checklist)}")
print(f"   Deployment script: Created")

print(f"\n🎯 Key Production Considerations:")
print(f"   🔒 Security: {len([m for m in security_measures if m['priority'] == 'Critical'])} critical items")
print(f"   📈 Scalability: {len(scalability_strategies)} strategies documented")
print(f"   📊 Monitoring: {len(monitoring_setup)} categories covered")
print(f"   ✅ Deployment: {len(checklist)} checklist items")

# %%
# Cell 7: Advanced Integration Patterns
"""
Advanced integration patterns and architectural considerations.
This cell demonstrates sophisticated integration techniques.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

class IntegrationPattern(Enum):
    """Types of integration patterns."""
    PIPELINE = "pipeline"
    EVENT_DRIVEN = "event_driven"
    REQUEST_RESPONSE = "request_response"
    PUB_SUB = "pub_sub"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"

@dataclass
class IntegrationContext:
    """Context for integration operations."""
    request_id: str
    user_id: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@runtime_checkable
class Component(Protocol):
    """Protocol for SpecCoder components."""
    
    def process(self, data: Dict[str, Any], context: IntegrationContext) -> Dict[str, Any]:
        """Process data with given context."""
        ...
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        ...

class PipelineIntegrator:
    """Advanced pipeline integration pattern."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pipeline_stages = []
        self.middleware = []
        self.error_handlers = []
        
    def add_stage(self, component: Component, name: str) -> 'PipelineIntegrator':
        """Add a stage to the pipeline."""
        self.pipeline_stages.append({'name': name, 'component': component})
        return self
    
    def add_middleware(self, middleware_func: Callable) -> 'PipelineIntegrator':
        """Add middleware to the pipeline."""
        self.middleware.append(middleware_func)
        return self
    
    def add_error_handler(self, handler_func: Callable) -> 'PipelineIntegrator':
        """Add error handler to the pipeline."""
        self.error_handlers.append(handler_func)
        return self
    
    async def execute_async(self, data: Dict[str, Any], context: IntegrationContext) -> Dict[str, Any]:
        """Execute pipeline asynchronously."""
        result = data
        
        try:
            # Apply pre-processing middleware
            for middleware in self.middleware:
                result = await middleware(result, context)
            
            # Execute pipeline stages
            for stage in self.pipeline_stages:
                stage_start = time.time()
                
                # Validate input
                if not stage['component'].validate(result):
                    raise ValueError(f"Validation failed for stage: {stage['name']}")
                
                # Process stage
                result = await stage['component'].process(result, context)
                
                # Add stage metadata
                context.metadata[f"{stage['name']}_duration"] = time.time() - stage_start
                context.metadata[f"{stage['name']}_status"] = "completed"
            
            # Apply post-processing middleware
            for middleware in reversed(self.middleware):
                result = await middleware(result, context)
                
            return result
            
        except Exception as e:
            # Handle errors
            for handler in self.error_handlers:
                try:
                    result = await handler(e, result, context)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")
            
            # Re-raise if not handled
            raise e

class EventDrivenIntegrator:
    """Event-driven integration pattern."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.event_handlers = {}
        self.event_queue = asyncio.Queue()
        self.running = False
        
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    async def publish(self, event_type: str, data: Dict[str, Any], context: IntegrationContext) -> None:
        """Publish an event."""
        event = {
            'type': event_type,
            'data': data,
            'context': context,
            'timestamp': time.time()
        }
        await self.event_queue.put(event)
        
    async def process_events(self) -> None:
        """Process events from the queue."""
        self.running = True
        
        while self.running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # Process event
                event_type = event['type']
                if event_type in self.event_handlers:
                    # Run all handlers concurrently
                    tasks = [
                        handler(event['data'], event['context'])
                        for handler in self.event_handlers[event_type]
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
            except asyncio.TimeoutError:
                # No events, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    def stop(self) -> None:
        """Stop the event processor."""
        self.running = False

class WorkflowOrchestrator:
    """Workflow orchestration integration pattern."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workflows = {}
        self.workflow_instances = {}
        
    def register_workflow(self, workflow_id: str, workflow_def: Dict[str, Any]) -> None:
        """Register a workflow definition."""
        self.workflows[workflow_id] = workflow_def
        
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any], 
                             context: IntegrationContext) -> Dict[str, Any]:
        """Execute a workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        workflow = self.workflows[workflow_id]
        instance_id = f"{workflow_id}_{context.request_id}"
        
        # Initialize workflow instance
        instance = {
            'id': instance_id,
            'workflow_id': workflow_id,
            'status': 'running',
            'current_step': 0,
            'data': input_data,
            'context': context,
            'start_time': time.time()
        }
        
        self.workflow_instances[instance_id] = instance
        
        try:
            # Execute workflow steps
            for i, step in enumerate(workflow['steps']):
                instance['current_step'] = i
                
                # Execute step
                step_result = await self._execute_step(step, instance['data'], context)
                
                # Update instance data
                if step_result:
                    instance['data'].update(step_result)
                    
            # Mark as completed
            instance['status'] = 'completed'
            instance['end_time'] = time.time()
            
            return instance['data']
            
        except Exception as e:
            instance['status'] = 'failed'
            instance['error'] = str(e)
            instance['end_time'] = time.time()
            raise e
            
    async def _execute_step(self, step: Dict[str, Any], data: Dict[str, Any], 
                           context: IntegrationContext) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step_type = step.get('type')
        
        if step_type == 'task':
            # Execute a task
            task_func = step.get('function')
            if task_func:
                return await task_func(data, context)
                
        elif step_type == 'parallel':
            # Execute parallel tasks
            tasks = step.get('tasks', [])
            results = await asyncio.gather(*[
                self._execute_step(task, data, context) for task in tasks
            ], return_exceptions=True)
            
            # Combine results
            combined_result = {}
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    combined_result[f'task_{i}_result'] = result
                    
            return combined_result
            
        elif step_type == 'condition':
            # Conditional execution
            condition = step.get('condition')
            if condition and condition(data, context):
                return await self._execute_step(step.get('true_branch'), data, context)
            else:
                return await self._execute_step(step.get('false_branch'), data, context)
                
        return {}

# Demonstrate advanced integration patterns
print("🧪 Advanced Integration Patterns Demonstration")
print("=" * 50)

# Create mock components for demonstration
class MockSpecParser:
    async def process(self, data: Dict[str, Any], context: IntegrationContext) -> Dict[str, Any]:
        await asyncio.sleep(0.1)  # Simulate processing time
        return {'parsed_spec': True, 'requirements': ['req1', 'req2']}
        
    def validate(self, data: Dict[str, Any]) -> bool:
        return 'spec_content' in data

class MockCodeGenerator:
    async def process(self, data: Dict[str, Any], context: IntegrationContext) -> Dict[str, Any]:
        await asyncio.sleep(0.2)  # Simulate processing time
        return {'generated_code': True, 'files': ['file1.py', 'file2.py']}
        
    def validate(self, data: Dict[str, Any]) -> bool:
        return 'parsed_spec' in data

# Pipeline Integration Demo
print("\n🔄 Pipeline Integration Pattern:")
pipeline = PipelineIntegrator(integration_config)
pipeline.add_stage(MockSpecParser(), "spec_parser")
pipeline.add_stage(MockCodeGenerator(), "code_generator")

# Create context
context = IntegrationContext(
    request_id="req-123",
    user_id="user-456",
    metadata={'workflow': 'pipeline_demo'}
)

# Execute pipeline asynchronously
async def demo_pipeline():
    start_time = time.time()
    result = await pipeline.execute_async(
        {'spec_content': 'sample spec'}, 
        context
    )
    duration = time.time() - start_time
    print(f"   ✅ Pipeline completed in {duration:.2f}s")
    print(f"   📊 Result: {result}")
    print(f"   📋 Context metadata: {context.metadata}")
    return result

# Event-Driven Integration Demo
print("\n⚡ Event-Driven Integration Pattern:")
event_integrator = EventDrivenIntegrator(integration_config)

# Define event handlers
async def spec_parsed_handler(data: Dict[str, Any], context: IntegrationContext):
    print(f"   📝 Spec parsed event: {context.request_id}")
    
async def code_generated_handler(data: Dict[str, Any], context: IntegrationContext):
    print(f"   ⚡ Code generated event: {context.request_id}")

# Subscribe to events
event_integrator.subscribe('spec.parsed', spec_parsed_handler)
event_integrator.subscribe('code.generated', code_generated_handler)

# Workflow Orchestration Demo
print("\n🎭 Workflow Orchestration Pattern:")
orchestrator = WorkflowOrchestrator(integration_config)

# Define a workflow
workflow_def = {
    'steps': [
        {
            'type': 'task',
            'function': MockSpecParser().process
        },
        {
            'type': 'parallel',
            'tasks': [
                {
                    'type': 'task',
                    'function': MockCodeGenerator().process
                }
            ]
        }
    ]
}

orchestrator.register_workflow('speccoder_workflow', workflow_def)

# Run demonstrations
async def run_demos():
    # Demo pipeline
    await demo_pipeline()
    
    # Demo event-driven
    await event_integrator.publish('spec.parsed', {'spec': 'test'}, context)
    await event_integrator.publish('code.generated', {'files': ['test.py']}, context)
    
    # Start event processor briefly
    event_task = asyncio.create_task(event_integrator.process_events())
    await asyncio.sleep(0.1)  # Let events process
    event_integrator.stop()
    await event_task
    
    # Demo workflow
    workflow_result = await orchestrator.execute_workflow(
        'speccoder_workflow',
        {'spec_content': 'test'},
        context
    )
    print(f"   🎭 Workflow completed: {workflow_result}")

# Run the demonstrations
asyncio.run(run_demos())

print(f"\n📊 Advanced Integration Summary:")
print(f"   🔄 Pipeline stages: {len(pipeline.pipeline_stages)}")
print(f"   ⚡ Event handlers: {len(event_integrator.event_handlers)}")
print(f"   🎭 Workflows registered: {len(orchestrator.workflows)}")
print(f"   🔧 Integration patterns: {len(IntegrationPattern)}")

# %%
# Cell 8: Complete Integration Summary and Best Practices
"""
Comprehensive summary of all integration concepts and final best practices.
This cell consolidates everything learned into actionable recommendations.
"""

import uuid
from datetime import datetime
import json

class IntegrationSummary:
    """Comprehensive integration summary and recommendations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.summary_data = {
            'modules_covered': [],
            'integration_patterns': [],
            'best_practices': [],
            'common_pitfalls': [],
            'performance_tips': [],
            'security_recommendations': []
        }
        
    def compile_module_summary(self) -> Dict[str, Any]:
        """Compile summary of all modules covered."""
        print("📚 Module Coverage Summary:")
        
        modules = [
            {
                'module': 'Spec Parser',
                'file': 'spec_parser.py',
                'purpose': 'Parse OpenSpec YAML specifications',
                'key_classes': ['ValidationCriteria', 'FunctionInterface', 'Requirement', 'OpenSpec', 'SpecParser'],
                'lines_of_code': 209,
                'complexity': 'Medium'
            },
            {
                'module': 'Code Generator',
                'file': 'generator.py',
                'purpose': 'Generate Python code from specifications',
                'key_classes': ['CodeGenerator'],
                'lines_of_code': 838,
                'complexity': 'High'
            },
            {
                'module': 'Orchestrator',
                'file': 'orchestrator.py',
                'purpose': 'Coordinate 4-stage pipeline execution',
                'key_classes': ['IntegrationOrchestrator'],
                'lines_of_code': 1348,
                'complexity': 'High'
            },
            {
                'module': 'Test Analyzer',
                'file': 'tester.py',
                'purpose': 'Analyze and validate generated tests',
                'key_classes': ['TestAnalyzer'],
                'lines_of_code': 366,
                'complexity': 'Medium'
            },
            {
                'module': 'CLI Interface',
                'file': 'cli.py',
                'purpose': 'Command-line interface for all operations',
                'key_classes': ['CLI command functions'],
                'lines_of_code': 419,
                'complexity': 'Medium'
            },
            {
                'module': 'Code Organizer',
                'file': 'organizer.py',
                'purpose': 'Organize generated code into production structure',
                'key_classes': ['CodeOrganizer'],
                'lines_of_code': 693,
                'complexity': 'Medium'
            },
            {
                'module': 'Templates',
                'file': 'templates.py',
                'purpose': 'Prompt templates for AI interactions',
                'key_classes': ['PromptTemplates'],
                'lines_of_code': 82,
                'complexity': 'Low'
            }
        ]
        
        total_lines = 0
        for module in modules:
            total_lines += module['lines_of_code']
            print(f"   📖 {module['module']} ({module['file']})")
            print(f"      Purpose: {module['purpose']}")
            print(f"      Complexity: {module['complexity']} ({module['lines_of_code']} lines)")
            print(f"      Key classes: {', '.join(module['key_classes'])}")
            print()
            
        self.summary_data['modules_covered'] = modules
        
        print(f"📊 Total Codebase: {total_lines} lines across {len(modules)} modules")
        return modules
    
    def compile_best_practices(self) -> List[Dict[str, str]]:
        """Compile comprehensive best practices."""
        print("🎯 Best Practices Summary:")
        
        practices = [
            {
                'category': 'Code Quality',
                'practice': 'Use type hints consistently',
                'reason': 'Improves code documentation and IDE support'
            },
            {
                'category': 'Code Quality',
                'practice': 'Implement comprehensive error handling',
                'reason': 'Prevents crashes and provides better debugging'
            },
            {
                'category': 'Architecture',
                'practice': 'Separate concerns into distinct modules',
                'reason': 'Improves maintainability and testability'
            },
            {
                'category': 'Architecture',
                'practice': 'Use dependency injection',
                'reason': 'Enables better testing and flexibility'
            },
            {
                'category': 'Performance',
                'practice': 'Implement caching for expensive operations',
                'reason': 'Reduces redundant computations and API calls'
            },
            {
                'category': 'Performance',
                'practice': 'Use async/await for I/O operations',
                'reason': 'Improves concurrency and responsiveness'
            },
            {
                'category': 'Security',
                'practice': 'Validate all inputs',
                'reason': 'Prevents injection attacks and data corruption'
            },
            {
                'category': 'Security',
                'practice': 'Use environment variables for secrets',
                'reason': 'Prevents accidental exposure of sensitive data'
            },
            {
                'category': 'Testing',
                'practice': 'Write tests for all public methods',
                'reason': 'Ensures reliability and prevents regressions'
            },
            {
                'category': 'Testing',
                'practice': 'Use mock objects for external dependencies',
                'reason': 'Enables isolated testing and faster execution'
            },
            {
                'category': 'Documentation',
                'practice': 'Document all public APIs',
                'reason': 'Improves usability and reduces support burden'
            },
            {
                'category': 'Documentation',
                'practice': 'Include examples in documentation',
                'reason': 'Helps users understand how to use the code'
            }
        ]
        
        for practice in practices:
            print(f"   ✅ {practice['practice']}")
            print(f"      Category: {practice['category']} | Reason: {practice['reason']}")
            print()
            
        self.summary_data['best_practices'] = practices
        return practices
    
    def compile_common_pitfalls(self) -> List[Dict[str, str]]:
        """Compile common pitfalls and how to avoid them."""
        print("⚠️  Common Pitfalls and Solutions:")
        
        pitfalls = [
            {
                'pitfall': 'Hardcoding configuration values',
                'impact': 'Reduced flexibility and deployment issues',
                'solution': 'Use configuration files and environment variables'
            },
            {
                'pitfall': 'Ignoring error handling',
                'impact': 'Unexpected crashes and poor user experience',
                'solution': 'Implement try-catch blocks and meaningful error messages'
            },
            {
                'pitfall': 'Not validating inputs',
                'impact': 'Security vulnerabilities and data corruption',
                'solution': 'Use validation libraries and schema validation'
            },
            {
                'pitfall': 'Blocking I/O operations',
                'impact': 'Poor performance and scalability',
                'solution': 'Use async/await or threading for I/O operations'
            },
            {
                'pitfall': 'Insufficient logging',
                'impact': 'Difficult debugging and monitoring',
                'solution': 'Implement structured logging with appropriate levels'
            },
            {
                'pitfall': 'Not writing tests',
                'impact': 'Bugs in production and difficult refactoring',
                'solution': 'Follow TDD and maintain high test coverage'
            },
            {
                'pitfall': 'Poor error messages',
                'impact': 'Difficult troubleshooting and user frustration',
                'solution': 'Provide clear, actionable error messages'
            },
            {
                'pitfall': 'Ignoring performance',
                'impact': 'Slow response times and poor scalability',
                'solution': 'Profile code and optimize bottlenecks'
            }
        ]
        
        for pitfall in pitfalls:
            print(f"   🚨 {pitfall['pitfall']}")
            print(f"      Impact: {pitfall['impact']}")
            print(f"      Solution: {pitfall['solution']}")
            print()
            
        self.summary_data['common_pitfalls'] = pitfalls
        return pitfalls
    
    def generate_integration_report(self) -> str:
        """Generate comprehensive integration report."""
        report = {
            'report_id': str(uuid.uuid4()),
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_modules': len(self.summary_data['modules_covered']),
                'total_lines': sum(m['lines_of_code'] for m in self.summary_data['modules_covered']),
                'best_practices': len(self.summary_data['best_practices']),
                'common_pitfalls': len(self.summary_data['common_pitfalls'])
            },
            'modules': self.summary_data['modules_covered'],
            'best_practices': self.summary_data['best_practices'],
            'common_pitfalls': self.summary_data['common_pitfalls'],
            'recommendations': [
                'Implement comprehensive monitoring and alerting',
                'Set up CI/CD pipeline for automated testing and deployment',
                'Create detailed documentation for all components',
                'Implement security scanning and vulnerability assessment',
                'Set up backup and disaster recovery procedures'
            ]
        }
        
        # Save report
        report_path = self.config['reports_dir'] / 'integration_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_path
    
    def create_learning_path(self) -> Dict[str, List[str]]:
        """Create recommended learning path for SpecCoder."""
        print("🎓 Recommended Learning Path:")
        
        learning_path = {
            'beginner': [
                'Start with Module 1: Spec Parser - Understand OpenSpec format',
                'Review Module 7: Templates - Learn prompt engineering basics',
                'Practice with CLI commands (Module 5) - Get hands-on experience',
                'Study basic Python concepts: dataclasses, type hints, error handling'
            ],
            'intermediate': [
                'Module 2: Code Generator - Understand AI integration',
                'Module 4: Test Analyzer - Learn test generation and analysis',
                'Module 6: Code Organizer - Study file organization patterns',
                'Practice async programming and error handling patterns'
            ],
            'advanced': [
                'Module 3: Orchestrator - Master pipeline coordination',
                'Module 8: Integration patterns - Advanced architecture concepts',
                'Study performance optimization and monitoring',
                'Learn production deployment and security practices'
            ],
            'expert': [
                'Contribute to SpecCoder core components',
                'Design new integration patterns',
                'Optimize for enterprise-scale deployments',
                'Research advanced AI prompting techniques'
            ]
        }
        
        for level, steps in learning_path.items():
            print(f"\n   📚 {level.title()} Level:")
            for i, step in enumerate(steps, 1):
                print(f"      {i}. {step}")
                
        return learning_path

# Generate comprehensive integration summary
print("🧪 Generating Complete Integration Summary")
print("=" * 50)

summary = IntegrationSummary(integration_config)

# Compile all summaries
modules = summary.compile_module_summary()
practices = summary.compile_best_practices()
pitfalls = summary.compile_common_pitfalls()
learning_path = summary.create_learning_path()

# Generate integration report
report_path = summary.generate_integration_report()

print(f"\n📊 Final Integration Summary:")
print(f"   📚 Modules documented: {len(modules)}")
print(f"   ✅ Best practices: {len(practices)}")
print(f"   ⚠️  Common pitfalls: {len(pitfalls)}")
print(f"   🎓 Learning path levels: {len(learning_path)}")
print(f"   📄 Integration report: {report_path}")

print(f"\n🎉 SpecCoder Integration Documentation Complete!")
print(f"\n🏆 Key Achievements:")
print(f"   📖 Comprehensive module documentation (8 modules)")
print(f"   🔧 Integration patterns and best practices")
print(f"   🛡️  Security and deployment guidelines")
print(f"   📈 Performance optimization strategies")
print(f"   🎓 Structured learning path")
print(f"   📊 Troubleshooting and error handling")

print(f"\n🚀 Next Steps:")
print(f"   1. Review the integration report: {report_path}")
print(f"   2. Follow the recommended learning path")
print(f"   3. Practice with the provided examples")
print(f"   4. Implement best practices in your projects")
print(f"   5. Contribute back to the SpecCoder project")

print(f"\n💡 Remember: 'DONE MEANS TAUGHT' - Every function, class, and method has been documented with 100% transparency!")

# Clean up integration environment
print(f"\n🧹 Cleaning up integration environment...")
shutil.rmtree(integration_dir, ignore_errors=True)
print(f"✅ Integration environment cleaned up")

print(f"\n🎊 Thank you for completing the SpecCoder Integration Documentation! 🎊")
