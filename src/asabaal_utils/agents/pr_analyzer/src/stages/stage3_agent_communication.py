#!/usr/bin/env python3
"""
Stage 3: Agent Communication Testing
Test robust agent communication with file-based prompts and clean formatting
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from asabaal_utils.agentic_toolkit.backend_config import BackendManager

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add shared utilities to path
shared_path = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "asabaal_utils" / "shared"
sys.path.insert(0, str(shared_path))

from api_confirmation import require_paid_api_confirmation

# Import backend manager
try:
    from asabaal_utils.shared.agentic_toolkit.backend_config import BackendManager, list_available_backends
    BACKEND_MANAGER_AVAILABLE = True
except ImportError:
    BACKEND_MANAGER_AVAILABLE = False
    BackendManager = None  # type: ignore
    list_available_backends = None  # type: ignore


class AgentCallResult(Enum):
    """Agent call result types"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    NO_TOKEN = "no_token"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass 
class AgentResponse:
    """Agent response with full debugging info"""
    agent_name: str
    result_type: AgentCallResult
    response_text: str
    error_message: str
    call_duration_ms: float
    prompt_length: int
    stdout: str
    stderr: str
    return_code: int


class RobustAgentCaller:
    """Robust agent communication system with file-based prompts"""
    
    def __init__(self, output_dir: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        if output_dir:
            self.test_output_dir = Path(output_dir) / "debug_outputs" / "stage3"
        else:
            self.test_output_dir = Path(__file__).parent / "debug_outputs" / "stage3"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create prompt data directory
        self.prompt_data_dir = self.test_output_dir / "prompt_data"
        self.prompt_data_dir.mkdir(exist_ok=True)
        
        # Load context from Stage 1 in the current output directory
        if output_dir:
            stage1_dir = Path(output_dir) / "debug_outputs" / "stage1"
        else:
            stage1_dir = Path(__file__).parent / "debug_outputs" / "stage1"
        context_file = stage1_dir / "final_analysis_context.json"
        
        if not context_file.exists():
            raise RuntimeError("Stage 1 context not found - run Stage 1 first!")
        
        with open(context_file, 'r') as f:
            self.analysis_context = json.load(f)
        
        # Initialize backend manager
        self.backend_manager = None
        
        if BACKEND_MANAGER_AVAILABLE:
            try:
                from asabaal_utils.agentic_toolkit.backend_config import BackendManager, list_available_backends, BackendConfig, BackendType
                
                # Create backend config from provided config or auto-detect
                backend_config = None
                if config and 'agentic_backend' in config:
                    backend_cfg = config['agentic_backend']
                    provider = backend_cfg.get('provider', 'ollama')
                    model = backend_cfg.get('model', 'anthropic/claude-3.5-sonnet')
                    
                    if provider == 'ollama':
                        backend_config = BackendConfig(
                            backend_type=BackendType.OLLAMA,
                            model=model,
                            base_url='http://localhost:11434'
                        )
                    elif provider == 'openrouter':
                        backend_config = BackendConfig(
                            backend_type=BackendType.OPENROUTER,
                            model=model,
                            api_key=os.getenv('OPENROUTER_API_KEY')
                        )
                    elif provider == 'claude':
                        backend_config = BackendConfig(
                            backend_type=BackendType.CLAUDE,
                            model=model,
                            api_key=os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
                        )
                
                self.backend_manager = BackendManager(backend_config)
                
                # Show available backends
                available_backends = list_available_backends()
                backend_info = self.backend_manager.get_backend_info()
                
                print(f"🔧 Agent Communication System initialized:")
                print(f"   Using {backend_info['backend_type']} backend with model {backend_info['model']}")
                print(f"   Context loaded: {len(self.analysis_context['files'])} files")
                print(f"   Backend available: {'Yes' if backend_info['available'] else 'No'}")
                print(f"   Prompt data directory: {self.prompt_data_dir}")
                
                # Show all available backends
                print(f"   Available backends:")
                for name, info in available_backends.items():
                    status = "✅" if info['available'] else "❌"
                    print(f"     {status} {name}")
                    
            except Exception as e:
                print(f"⚠️  Backend manager initialization failed: {e}")
                self.backend_manager = None
        else:
            print(f"🔧 Agent Communication System initialization failed:")
            print(f"   Backend manager not available")
            print(f"   Context loaded: {len(self.analysis_context['files'])} files")
            print(f"   Prompt data directory: {self.prompt_data_dir}")
    
    def test_environment_setup(self) -> Dict[str, Any]:
        """Test environment setup and prerequisites"""
        print("\n🔧 Testing Environment Setup...")
        
        setup_results = {
            'backend_manager_available': False,
            'backend_client_ready': False,
            'backend_type': None,
            'backend_model': None,
            'environment_ready': False,
            'available_backends': {},
            'issues': []
        }
        
        # Test 1: Check backend manager availability
        if BACKEND_MANAGER_AVAILABLE and self.backend_manager:
            setup_results['backend_manager_available'] = True
            backend_info = self.backend_manager.get_backend_info()
            setup_results['backend_type'] = backend_info['backend_type']
            setup_results['backend_model'] = backend_info['model']
            
            print(f"   ✅ Backend manager available")
            print(f"   📡 Using {backend_info['backend_type']} backend")
            print(f"   🤖 Model: {backend_info['model']}")
            
            # Test backend client
            if backend_info['available']:
                setup_results['environment_ready'] = True
                print(f"   ✅ Backend client available")
                print(f"   ✅ Environment ready ({backend_info['backend_type']} provider available)")
                
                # Test backend client (optional, for debugging)
                try:
                    test_prompt = "Reply with just 'test successful' and nothing else."
                    response = self.backend_manager.ask(test_prompt)
                    
                    if response and hasattr(response, 'content') and 'test successful' in response.content.lower():
                        setup_results['backend_client_ready'] = True
                        print(f"   ✅ Backend client test successful")
                    else:
                        setup_results['issues'].append("Backend client test failed (but client is available)")
                        print(f"   ⚠️  Backend client test failed (but client is available)")
                        
                except Exception as e:
                    setup_results['issues'].append(f"Backend client test error: {e}")
                    print(f"   ⚠️  Backend client test error: {e}")
            else:
                setup_results['issues'].append("Backend client not available")
                print(f"   ❌ Backend client not available")
                
            # List all available backends
            if list_available_backends:
                setup_results['available_backends'] = list_available_backends()
                
        else:
            setup_results['issues'].append("Backend manager not available")
            print(f"   ❌ Backend manager not available")
        
        # Save environment test results
        with open(self.test_output_dir / "environment_test.json", 'w') as f:
            json.dump(setup_results, f, indent=2)
        
        return setup_results
    
    def create_duplicate_detection_prompt(self) -> str:
        """Create duplicate detection prompt with file references"""
        
        # Save detailed file analysis to a file
        file_analysis_data = {
            'pr_summary': self.analysis_context['pr_summary'],
            'categories': {},
            'file_details': []
        }
        
        # Organize files by category with content
        for category, files in self.analysis_context['categories'].items():
            if not files or category == 'GENERATED_IRRELEVANT':
                continue
                
            file_analysis_data['categories'][category] = len(files)
            
            # Add detailed file info for analysis
            for file_data in files[:10]:  # Limit per category
                file_details = {
                    'path': file_data['path'],
                    'category': category,
                    'change_type': file_data['change_type'],
                    'lines_added': file_data['lines_added'],
                    'lines_removed': file_data['lines_removed'],
                    'size': file_data['size'],
                    'content_sample': file_data.get('content_sample', ''),
                    'has_functions': file_data.get('has_functions', False),
                    'has_classes': file_data.get('has_classes', False)
                }
                file_analysis_data['file_details'].append(file_details)
        
        # Save data file (for debugging)
        data_file = self.prompt_data_dir / "duplicate_analysis_data.json"
        with open(data_file, 'w') as f:
            json.dump(file_analysis_data, f, indent=2)
        
        # Create clean prompt with JSON content inline
        json_content = json.dumps(file_analysis_data, indent=2)
        prompt = f"""You are a senior software architect detecting duplicate files.

Here is the detailed file analysis data:

```json
{json_content}
```

Instructions:
1. Analyze the JSON data above which contains PR summary, file categories, and detailed file information
2. Analyze file content samples and purposes to find duplicates
3. Focus on functional duplicates - files that solve the same problems

Expected duplicates based on manual analysis:
- Blog processing scripts in content/ directory
- Database setup files (supabase-setup.sql, etc.) 
- Deployment guides (VERCEL-DEPLOY.md variants)

Provide your response in this exact format:

## CRITICAL:
[Exact duplicates or abandoned implementations with specific file paths]

## HIGH:
[Functional duplicates with different implementations and file paths]

## MEDIUM:
[Similar purpose, potentially consolidatable files]

## Summary:
[Brief summary of duplicate analysis findings]

Be specific about which files and provide evidence from the content samples."""

        return prompt
    
    def create_merge_readiness_prompt(self) -> str:
        """Create merge readiness prompt with inline JSON content"""
        
        # Save PR analysis data
        pr_data = {
            'pr_summary': self.analysis_context['pr_summary'],
            'category_breakdown': {
                cat: len(files) for cat, files in self.analysis_context['categories'].items()
            },
            'sample_files': [
                {
                    'path': f['path'],
                    'category': f['category'],
                    'change_type': f['change_type'],
                    'lines_added': f['lines_added'],
                    'lines_removed': f['lines_removed'],
                    'content_preview': f.get('content_sample', '')[:200]
                }
                for f in self.analysis_context['files'][:20]
            ]
        }
        
        # Save data file (for debugging)
        data_file = self.prompt_data_dir / "merge_readiness_data.json"
        with open(data_file, 'w') as f:
            json.dump(pr_data, f, indent=2)
        
        # Create prompt with inline JSON content
        json_content = json.dumps(pr_data, indent=2)
        prompt = f"""You are a senior engineering manager evaluating merge readiness.

Here is the PR analysis data:

```json
{json_content}
```

Instructions:
1. Analyze the JSON data above which contains PR summary, categories, and sample files
2. Evaluate completeness, code quality, and risks
3. This is a massive PR with 257 files and significant line changes

Assessment criteria:
- COMPLETENESS: Unfinished work, TODOs, placeholders
- CODE QUALITY: Consistency, obvious issues, appropriate scope  
- RISK: Large-scale changes, breaking changes, deployment risks
- ORGANIZATION: Mixed concerns, experimental code

Provide your response in this exact JSON format:
{{
  "merge_readiness_score": <number 0-100>,
  "status": "<READY|REVIEW_NEEDED|NOT_READY>", 
  "blocking_issues": <number>,
  "warning_issues": <number>,
  "recommendation": "<brief summary>",
  "key_concerns": ["<concern1>", "<concern2>"]
}}"""

        return prompt
    
    def create_pattern_analysis_prompt(self) -> str:
        """Create pattern analysis prompt with inline JSON content"""
        
        # Save pattern analysis data
        pattern_data = {
            'file_categories': list(self.analysis_context['categories'].keys()),
            'sample_files_by_category': {}
        }
        
        # Sample files from each category for pattern analysis
        for category, files in self.analysis_context['categories'].items():
            if files and category != 'GENERATED_IRRELEVANT':
                pattern_data['sample_files_by_category'][category] = [
                    {
                        'path': f['path'],
                        'change_type': f['change_type'],
                        'content_preview': f.get('content_sample', '')[:300]
                    }
                    for f in files[:5]  # Max 5 per category
                ]
        
        # Save data file (for debugging)
        data_file = self.prompt_data_dir / "pattern_analysis_data.json"
        with open(data_file, 'w') as f:
            json.dump(pattern_data, f, indent=2)
        
        # Create prompt with inline JSON content
        json_content = json.dumps(pattern_data, indent=2)
        prompt = f"""You are a software architect analyzing code patterns and consistency.

Here is the pattern analysis data:

```json
{json_content}
```

Instructions:
1. Analyze the JSON data above which contains file categories and content samples
2. Look for naming convention inconsistencies
3. Identify different approaches to similar problems
4. Note architectural pattern inconsistencies

Focus areas:
- File naming patterns across categories
- Code style consistency within categories  
- Similar functionality implemented differently
- Missing architectural patterns

Provide your response in this exact format:

## CRITICAL:
[Critical pattern issues that must be fixed]

## HIGH:
[High priority consistency issues]

## MEDIUM:
[Medium priority improvements]

## Summary:
[Brief summary of pattern analysis findings]"""

        return prompt
    
    def call_agent_robust(self, agent_name: str, prompt: str, timeout_seconds: int = 300) -> AgentResponse:
        """Call agent with robust error handling and full debugging"""
        start_time = time.time()
        
        print(f"   🤖 Calling {agent_name} agent...")
        print(f"      Prompt length: {len(prompt):,} chars (file-based)")
        print(f"      Timeout: {timeout_seconds}s")
        
        # Use backend manager API
        if not self.backend_manager:
            end_time = time.time()
            call_duration = (end_time - start_time) * 1000
            
            return AgentResponse(
                agent_name=agent_name,
                result_type=AgentCallResult.NOT_FOUND,
                response_text="",
                error_message="Backend manager not available - check backend configuration",
                call_duration_ms=call_duration,
                prompt_length=len(prompt),
                stdout="",
                stderr="",
                return_code=-1
            )
        
        # Make backend API call
        try:
            backend_info = self.backend_manager.get_backend_info()
            backend_type = backend_info['backend_type']
            backend_model = backend_info.get('model', 'unknown')
            print(f"      Using {backend_type} API with model {backend_model}...")
            
            # Require confirmation for paid APIs
            if not require_paid_api_confirmation(backend_type):
                end_time = time.time()
                call_duration = (end_time - start_time) * 1000
                
                return AgentResponse(
                    agent_name=agent_name,
                    result_type=AgentCallResult.NOT_FOUND,
                    response_text="",
                    error_message="Paid API usage not confirmed by user",
                    call_duration_ms=call_duration,
                    prompt_length=len(prompt),
                    stdout="",
                    stderr="",
                    return_code=-1
                )
            
            response_text = self.backend_manager.call_agent(prompt, timeout=timeout_seconds)
            
            end_time = time.time()
            call_duration = (end_time - start_time) * 1000
            
            print(f"      ✅ {backend_type.title()} Success ({call_duration:.1f}ms)")
            print(f"      Response length: {len(response_text):,} chars")
            
            return AgentResponse(
                agent_name=agent_name,
                result_type=AgentCallResult.SUCCESS,
                response_text=response_text.strip(),
                error_message="",
                call_duration_ms=call_duration,
                prompt_length=len(prompt),
                stdout=response_text,
                stderr="",
                return_code=0
            )
            
        except Exception as e:
            end_time = time.time()
            call_duration = (end_time - start_time) * 1000
            
            # Get backend info for error messages
            backend_info = self.backend_manager.get_backend_info()
            backend_type = backend_info['backend_type']
            
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                print(f"      ⏰ Timeout after {timeout_seconds}s")
                result_type = AgentCallResult.TIMEOUT
                error_message = f"{backend_type.title()} API call timed out after {timeout_seconds} seconds"
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                print(f"      ❌ API Key Error")
                result_type = AgentCallResult.NO_TOKEN
                error_message = f"{backend_type.title()} API key invalid or missing"
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                print(f"      ❌ Network Error")
                result_type = AgentCallResult.NETWORK_ERROR
                error_message = f"{backend_type.title()} API network error: {error_msg}"
            else:
                print(f"      ❌ {backend_type.title()} API Error: {e}")
                result_type = AgentCallResult.UNKNOWN_ERROR
                error_message = f"{backend_type.title()} API error: {error_msg}"
            
            return AgentResponse(
                agent_name=agent_name,
                result_type=result_type,
                response_text="",
                error_message=error_message,
                call_duration_ms=call_duration,
                prompt_length=len(prompt),
                stdout="",
                stderr=error_msg,
                return_code=-1
            )
    
    def test_all_agents(self) -> Dict[str, AgentResponse]:
        """Test all agents with clean file-based prompts"""
        print("\n🤖 Testing Agent Communication...")
        
        # Create prompts
        prompts = {
            'duplicate_detection': self.create_duplicate_detection_prompt(),
            'merge_readiness': self.create_merge_readiness_prompt(),
            'pattern_analysis': self.create_pattern_analysis_prompt()
        }
        
        responses = {}
        
        for agent_name, prompt in prompts.items():
            print(f"\n   Testing {agent_name}:")
            
            # Save prompt for debugging
            with open(self.test_output_dir / f"{agent_name}_prompt.txt", 'w') as f:
                f.write(prompt)
            
            # Call agent
            response = self.call_agent_robust(agent_name, prompt, 300)
            responses[agent_name] = response
            
            # Save individual response
            response_debug = {
                'agent_name': response.agent_name,
                'result_type': response.result_type.value,
                'response_length': len(response.response_text),
                'error_message': response.error_message,
                'call_duration_ms': response.call_duration_ms,
                'prompt_length': response.prompt_length,
                'return_code': response.return_code,
                'response_preview': response.response_text[:1000] if response.response_text else "",
                'stderr_preview': response.stderr[:500] if response.stderr else ""
            }
            
            with open(self.test_output_dir / f"{agent_name}_response_debug.json", 'w') as f:
                json.dump(response_debug, f, indent=2)
            
            # Save full response text if available
            if response.response_text:
                with open(self.test_output_dir / f"{agent_name}_full_response.txt", 'w') as f:
                    f.write(response.response_text)
        
        return responses
    
    def analyze_communication_results(self, responses: Dict[str, AgentResponse]) -> Dict[str, Any]:
        """Analyze agent communication results"""
        print("\n📊 Analyzing Communication Results...")
        
        analysis = {
            'total_agents': len(responses),
            'successful_calls': 0,
            'failed_calls': 0,
            'average_response_time_ms': 0,
            'failure_types': {},
            'recommendations': [],
            'results_by_agent': {}
        }
        
        total_time = 0
        
        for agent_name, response in responses.items():
            # Count results
            if response.result_type == AgentCallResult.SUCCESS:
                analysis['successful_calls'] += 1
            else:
                analysis['failed_calls'] += 1
                
                failure_type = response.result_type.value
                analysis['failure_types'][failure_type] = analysis['failure_types'].get(failure_type, 0) + 1
            
            total_time += response.call_duration_ms
            
            # Store individual results
            analysis['results_by_agent'][agent_name] = {
                'success': response.result_type == AgentCallResult.SUCCESS,
                'result_type': response.result_type.value,
                'response_length': len(response.response_text),
                'call_duration_ms': response.call_duration_ms,
                'error_summary': response.error_message[:100] if response.error_message else ""
            }
        
        # Calculate averages
        if responses:
            analysis['average_response_time_ms'] = total_time / len(responses)
        
        # Generate recommendations
        if analysis['failed_calls'] == 0:
            analysis['recommendations'].append("✅ All agent communications successful")
            analysis['status'] = "READY"
        else:
            analysis['status'] = "PARTIAL" if analysis['successful_calls'] > 0 else "NOT_READY"
            
            if 'not_found' in analysis['failure_types']:
                analysis['recommendations'].append("❌ Install openai package: pip install openai")
            
            if 'no_token' in analysis['failure_types']:
                if self.backend_manager:
                    backend_info = self.backend_manager.get_backend_info()
                    backend_type = backend_info['backend_type'].upper()
                    analysis['recommendations'].append(f"❌ Set {backend_type}_API_KEY environment variable")
                else:
                    analysis['recommendations'].append("❌ Set appropriate API_KEY environment variable")
            
            if 'network_error' in analysis['failure_types']:
                if self.backend_manager:
                    backend_info = self.backend_manager.get_backend_info()
                    backend_type = backend_info['backend_type'].title()
                    analysis['recommendations'].append(f"❌ Check internet connection and {backend_type} API status")
                else:
                    analysis['recommendations'].append("❌ Check internet connection and API status")
        
        # Success rate assessment
        success_rate = analysis['successful_calls'] / analysis['total_agents'] if analysis['total_agents'] > 0 else 0
        
        if success_rate == 1.0:
            analysis['recommendations'].append("🎉 Ready to proceed to Stage 4: Response Parsing")
        
        # Save analysis
        with open(self.test_output_dir / "communication_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Display results
        print(f"   Total agents: {analysis['total_agents']}")
        print(f"   Successful: {analysis['successful_calls']}")
        print(f"   Failed: {analysis['failed_calls']}")
        print(f"   Average response time: {analysis['average_response_time_ms']:.1f}ms")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Status: {analysis['status']}")
        
        if analysis['failure_types']:
            print(f"   Failure types:")
            for failure_type, count in analysis['failure_types'].items():
                print(f"     • {failure_type}: {count}")
        
        print(f"   Recommendations:")
        for rec in analysis['recommendations']:
            print(f"     • {rec}")
        
        return analysis
    
    def run_full_stage3_test(self) -> Dict[str, Any]:
        """Run complete Stage 3 testing pipeline"""
        print("=" * 60)
        print("🧪 STAGE 3: AGENT COMMUNICATION TESTING")
        print("=" * 60)
        
        # Test 1: Environment Setup
        env_results = self.test_environment_setup()
        
        # Test 2: Agent Communication
        if env_results['environment_ready']:
            print(f"✅ Environment ready - proceeding with agent tests")
            responses = self.test_all_agents()
        else:
            print(f"❌ Environment not ready - simulating agent failures")
            # Create mock failure responses for testing downstream stages
            responses = {}
            for agent_name in ['duplicate_detection', 'merge_readiness', 'pattern_analysis']:
                responses[agent_name] = AgentResponse(
                    agent_name=agent_name,
                    result_type=AgentCallResult.NOT_FOUND,
                    response_text="",
                    error_message="Environment not ready - AI backend client not available",
                    call_duration_ms=0,
                    prompt_length=0,
                    stdout="",
                    stderr="Environment not ready",
                    return_code=-1
                )
        
        # Test 3: Analyze Results
        analysis = self.analyze_communication_results(responses)
        
        # Save comprehensive stage results
        stage3_summary = {
            'stage': 'Agent Communication',
            'environment_setup': env_results,
            'communication_analysis': analysis,
            'individual_responses': {
                name: {
                    'success': resp.result_type == AgentCallResult.SUCCESS,
                    'result_type': resp.result_type.value,
                    'response_preview': resp.response_text[:200] if resp.response_text else "",
                    'error_message': resp.error_message
                }
                for name, resp in responses.items()
            },
            'ready_for_stage4': analysis['status'] in ['READY', 'PARTIAL']
        }
        
        with open(self.test_output_dir / "stage3_test_summary.json", 'w') as f:
            json.dump(stage3_summary, f, indent=2)
        
        print(f"\n✅ STAGE 3 COMPLETE:")
        print(f"   Environment ready: {env_results['environment_ready']}")
        print(f"   Agent success rate: {analysis['successful_calls']}/{analysis['total_agents']}")
        print(f"   Status: {analysis['status']}")
        print(f"   Debug outputs saved to: {self.test_output_dir}")
        
        return stage3_summary


def main():
    """Test Stage 3: Agent Communication"""
    try:
        caller = RobustAgentCaller()
        results = caller.run_full_stage3_test()
        
        if results['ready_for_stage4']:
            print(f"\n🎉 Stage 3 successful!")
            print(f"Ready to proceed to Stage 4: Response Parsing")
            
            # Show what we have for Stage 4
            if results['communication_analysis']['successful_calls'] > 0:
                print(f"\n📋 Available for Stage 4 testing:")
                for agent_name, resp_info in results['individual_responses'].items():
                    if resp_info['success']:
                        print(f"   ✅ {agent_name}: {len(resp_info['response_preview'])}+ char response")
                    else:
                        print(f"   ❌ {agent_name}: {resp_info['error_message']}")
        else:
            print(f"\n❌ Stage 3 failed - agent communication not working")
            print(f"Check environment setup and fix issues before proceeding")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Stage 3 testing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()