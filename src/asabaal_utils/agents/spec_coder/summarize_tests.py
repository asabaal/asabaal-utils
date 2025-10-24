"""
Test Summarizer - AI Analysis Layer

Uses Ollama to analyze parsed test data and generate natural language
descriptions of what each test implies about the required code behavior.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from asabaal_utils.agents.spec_coder.ollama_client import OllamaClient, GenerationConfig

logger = logging.getLogger(__name__)


@dataclass
class TestSummary:
    """Represents a test with its AI-generated behavior summary."""
    name: str
    target_function: Optional[str]
    inputs: Dict[str, Any]
    assertions: List[str]
    implied_behavior: str


class TestSummarizer:
    """Uses AI to summarize test implications."""
    
    def __init__(self, model_name: str = "qwen3-coder:latest", spec_file: Optional[Path] = None, source_file: Optional[Path] = None):
        """Initialize the summarizer with Ollama client and optional context files."""
        config = GenerationConfig(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0.1,
            max_tokens=512,
            top_p=0.9,
            top_k=40
        )
        self.client = OllamaClient(config)
        
        # Test connection
        if not self.client.test_connection():
            raise RuntimeError("Failed to connect to Ollama. Please ensure Ollama is running.")
        
        # Load context
        self.spec_context = self._load_spec_context(spec_file) if spec_file else ""
        self.source_context = self._load_source_context(source_file) if source_file else ""
    
    def _load_spec_context(self, spec_file: Path) -> str:
        """Load OpenSpec requirements as context."""
        try:
            import yaml
            with open(spec_file, 'r') as f:
                spec_data = yaml.safe_load(f)
            
            context = "OpenSpec Requirements:\n"
            for req in spec_data.get('requirements', []):
                context += f"- {req['id']}: {req['title']}\n"
                context += f"  Description: {req['description']}\n"
                if 'interface' in req:
                    iface = req['interface']
                    context += f"  Function: {iface['function']}({', '.join(iface['parameters'].keys())}) -> {iface['returns']}\n"
                context += "\n"
            return context
        except Exception as e:
            logger.warning(f"Failed to load spec context: {e}")
            return ""
    
    def _load_source_context(self, source_file: Path) -> str:
        """Load generated source code as context."""
        try:
            with open(source_file, 'r') as f:
                source_code = f.read()
            
            # Extract function signatures and docstrings
            context = "Generated Source Code:\n"
            import ast
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function signature
                    args = []
                    for arg in node.args.args:
                        args.append(arg.arg)
                    sig = f"def {node.name}({', '.join(args)})"
                    
                    # Get docstring
                    docstring = ast.get_docstring(node) or "No docstring"
                    
                    context += f"- {sig}\n"
                    context += f"  {docstring}\n\n"
            
            return context
        except Exception as e:
            logger.warning(f"Failed to load source context: {e}")
            return ""
    
    def create_summary_prompt(self, test_data) -> str:
        """Create a prompt for summarizing a single test."""
        # Handle both TestInfo objects and dictionaries
        if hasattr(test_data, 'name'):
            name = test_data.name
            target_function = test_data.target_function or 'Unknown'
            inputs = test_data.inputs
            assertions = test_data.assertions
        else:
            name = test_data.get('name', 'Unknown')
            target_function = test_data.get('target_function', 'Unknown')
            inputs = test_data.get('inputs', {})
            assertions = test_data.get('assertions', [])
        
        prompt = f"""You are analyzing a Python test to understand what behavior it requires from the function under test.

Context:
{self.spec_context}

{self.source_context}

Test Details:
- Test name: {name}
- Target function: {target_function}
- Inputs: {inputs}
- Assertions: {assertions}

Instructions:
1. Describe in 1-2 sentences what this test expects the function to do
2. Focus on the functional requirement being tested
3. Do not repeat these instructions
4. Do not mention the test name, inputs, or assertions
5. Respond ONLY with valid JSON

Example response:
{{"implied_behavior": "The function must validate input parameters and raise appropriate exceptions for invalid values."}}"""

        return prompt
    
    def summarize_test(self, test_data) -> Optional[str]:
        """Generate a behavior summary for a single test."""
        try:
            prompt = self.create_summary_prompt(test_data)
            response = self.client.generate(prompt)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                behavior = result.get('implied_behavior', '')
            except json.JSONDecodeError:
                # Fallback: try to extract from non-JSON response
                if 'implied_behavior' in response:
                    start = response.find('"implied_behavior":')
                    if start != -1:
                        start = response.find('"', start + 18) + 1
                        end = response.find('"', start)
                        if end != -1:
                            behavior = response[start:end]
                        else:
                            behavior = response
                    else:
                        behavior = response
                else:
                    behavior = response.strip()
            
            # Clean up the response
            if behavior:
                # Remove prompt instruction contamination
                if "Do not mention" in behavior:
                    # Find where the actual behavior starts
                    lines = behavior.split('\n')
                    clean_lines = []
                    for line in lines:
                        if not line.strip().startswith("Do not") and "Do not" not in line:
                            clean_lines.append(line)
                    behavior = '\n'.join(clean_lines).strip()
                
                # If still empty or contains instructions, provide a generic summary
                if not behavior or "Do not" in behavior or len(behavior) < 10:
                    target = test_data.get('target_function', 'the function')
                    return f"The function should handle edge cases and invalid inputs appropriately when {target} is called with unexpected parameters."
                
                # Limit length to prevent overly long responses
                if len(behavior) > 500:
                    behavior = behavior[:497] + "..."
                
                return behavior
            
            return "The function should handle edge cases and invalid inputs appropriately."
            
        except Exception as e:
            test_name = getattr(test_data, 'name', test_data.get('name', 'unknown'))
            logger.error(f"Failed to summarize test {test_name}: {e}")
            return f"Error generating summary: {str(e)}"
    
    def summarize_test_file(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize all tests in a parsed test file."""
        summarized_tests = []
        
        for test in parsed_data.get('tests', []):
            summary = self.summarize_test(test)
            
            # Handle both TestInfo objects and dictionaries
            if hasattr(test, 'name'):
                name = test.name
                target_function = test.target_function
                inputs = test.inputs
                assertions = test.assertions
            else:
                name = test.get('name', 'Unknown')
                target_function = test.get('target_function')
                inputs = test.get('inputs', {})
                assertions = test.get('assertions', [])
            
            summarized_test = {
                "name": name,
                "target_function": target_function,
                "inputs": inputs,
                "assertions": assertions,
                "implied_behavior": summary
            }
            summarized_tests.append(summarized_test)
        
        return {
            "file": parsed_data['file'],
            "tests": summarized_tests
        }
    
    def save_summary(self, summary_data: Dict[str, Any], output_path: Path):
        """Save the summary to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary saved to: {output_path}")


def main():
    """Command-line interface for the test summarizer."""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python summarize_tests.py <parsed_json_file> <output_directory>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load parsed test data
    with open(input_file, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # Handle single file or array of files
    if isinstance(parsed_data, list):
        # Multiple files
        for file_data in parsed_data:
            summarizer = TestSummarizer()
            summary = summarizer.summarize_test_file(file_data)
            
            output_path = output_dir / f"test_summary_{file_data['file']}.json"
            summarizer.save_summary(summary, output_path)
    
    else:
        # Single file
        summarizer = TestSummarizer()
        summary = summarizer.summarize_test_file(parsed_data)
        
        output_path = output_dir / f"test_summary_{parsed_data['file']}.json"
        summarizer.save_summary(summary, output_path)
    
    print(f"Summaries saved to {output_dir}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()