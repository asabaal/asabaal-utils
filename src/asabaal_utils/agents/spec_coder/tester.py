"""
Test Analyzer - Main Orchestrator

Combines AST parsing and AI summarization to analyze test files
and generate comprehensive behavior summaries.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from .parse_tests import parse_test_file
    from .summarize_tests import TestSummarizer
except ImportError:
    from parse_tests import parse_test_file
    from summarize_tests import TestSummarizer

logger = logging.getLogger(__name__)


class TestAnalyzer:
    """Main orchestrator for test analysis."""
    
    def __init__(self, model_name: str = "qwen3-coder:latest", spec_file: Optional[Path] = None, source_file: Optional[Path] = None):
        """Initialize the analyzer with a summarizer and context files."""
        self.summarizer = TestSummarizer(model_name, spec_file, source_file)
    
    def analyze_single_file(self, test_file_path: Path) -> Dict[str, Any]:
        """Analyze a single test file."""
        logger.info(f"Analyzing test file: {test_file_path}")
        
        # Step 1: Parse the test file with AST
        parsed_data = parse_test_file(test_file_path)
        
        if "error" in parsed_data:
            logger.error(f"Failed to parse {test_file_path}: {parsed_data['error']}")
            return parsed_data
        
        # Step 2: Summarize with AI
        summarized_data = self.summarizer.summarize_test_file(parsed_data)
        
        return summarized_data
    
    def analyze_directory(self, test_dir: Path, output_dir: Path) -> List[Dict[str, Any]]:
        """Analyze all test files in a directory."""
        logger.info(f"Analyzing test directory: {test_dir}")
        
        results = []
        test_files = list(test_dir.glob("test_*.py"))
        
        if not test_files:
            logger.warning(f"No test files found in {test_dir}")
            return results
        
        logger.info(f"Found {len(test_files)} test files")
        
        for test_file in test_files:
            try:
                analyzed_data = self.analyze_single_file(test_file)
                
                # Save individual summary
                output_path = output_dir / f"test_summary_{test_file.name}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(analyzed_data, f, indent=2, ensure_ascii=False)
                
                results.append(analyzed_data)
                logger.info(f"Saved summary for {test_file.name}")
                
            except Exception as e:
                logger.error(f"Failed to analyze {test_file}: {e}")
                results.append({
                    "file": test_file.name,
                    "error": str(e),
                    "tests": []
                })
        
        # Save combined summary
        combined_path = output_dir / "combined_test_summary.json"
        combined_data = {
            "analysis_summary": {
                "total_files": len(test_files),
                "successful_analyses": len([r for r in results if "error" not in r]),
                "failed_analyses": len([r for r in results if "error" in r]),
                "total_tests": sum(len(r.get("tests", [])) for r in results)
            },
            "files": results
        }
        
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved combined summary to {combined_path}")
        
        return results
    
    def generate_report(self, analyzed_data: List[Dict[str, Any]], output_path: Path):
        """Generate a markdown report from analyzed data."""
        report_lines = ["# Test Analysis Report\n"]
        
        # Summary section
        total_files = len(analyzed_data)
        total_tests = sum(len(data.get("tests", [])) for data in analyzed_data)
        
        report_lines.extend([
            "## Summary\n",
            f"- **Total test files analyzed**: {total_files}",
            f"- **Total tests found**: {total_tests}\n",
            "## Detailed Analysis\n"
        ])
        
        # Per-file analysis
        for data in analyzed_data:
            if "error" in data:
                report_lines.extend([
                    f"### {data['file']}\n",
                    f"❌ **Error**: {data['error']}\n"
                ])
                continue
            
            report_lines.append(f"### {data['file']}\n")
            
            if not data.get("tests"):
                report_lines.append("No tests found.\n")
                continue
            
            for test in data["tests"]:
                report_lines.extend([
                    f"#### {test['name']}\n",
                    f"- **Target function**: {test.get('target_function', 'Unknown')}",
                    f"- **Inputs**: {test['inputs']}",
                    f"- **Assertions**: {len(test['assertions'])} assertion(s)",
                    f"- **Implied behavior**: {test.get('implied_behavior', 'No summary available')}\n"
                ])
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Report saved to {output_path}")


def main():
    """Command-line interface for the test analyzer."""
    if len(sys.argv) != 2:
        print("Usage: python analyze_tests.py <test_file_or_directory>")
        sys.exit(1)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = Path(sys.argv[1])
    output_dir = Path("../analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to find context files
    spec_file = None
    source_file = None
    
    # Look for spec file in reference directory
    possible_spec = Path("../../reference/openspec/specs/rhythmic_pulse_generator.yml")
    if possible_spec.exists():
        spec_file = possible_spec
    
    # Look for source file in output directory
    possible_source = Path("../output/scaffolds/src/rhythmic_pulse_generator.py")
    if possible_source.exists():
        source_file = possible_source
    
    analyzer = TestAnalyzer(spec_file=spec_file, source_file=source_file)
    
    if spec_file:
        print(f"Using spec context: {spec_file}")
    if source_file:
        print(f"Using source context: {source_file}")
    
    if input_path.is_file():
        # Analyze single file
        result = analyzer.analyze_single_file(input_path)
        
        output_path = output_dir / f"test_summary_{input_path.name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Analysis complete. Output saved to {output_path}")
        
        # Generate report for single file
        analyzer.generate_report([result], output_dir / "test_analysis_report.md")
    
    elif input_path.is_dir():
        # Analyze directory
        results = analyzer.analyze_directory(input_path, output_dir)
        
        print(f"Analysis complete. Processed {len(results)} files.")
        print(f"Outputs saved to {output_dir}")
        
        # Generate combined report
        analyzer.generate_report(results, output_dir / "test_analysis_report.md")
    
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()