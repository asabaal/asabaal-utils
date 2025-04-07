#!/usr/bin/env python3
"""
GitHub Actions Test Log Parser

This script parses pytest output from GitHub Actions or local test runs
and extracts only the errors and failures for easier debugging.

Usage:
  # Parse from a file
  python parse_test_logs.py test_output.log
  
  # Parse from stdin (piping)
  pytest | python parse_test_logs.py
  
  # Save output to a file
  python parse_test_logs.py test_output.log --output errors.log
"""

import sys
import argparse
import os


def parse_test_logs(log_content):
    """
    Parse pytest logs and extract failures and errors.
    
    Args:
        log_content (str): The raw pytest log content
        
    Returns:
        dict: Dictionary with 'errors', 'failures', and 'summary' lists
    """
    results = {
        'errors': [],
        'failures': [],
        'summary': None
    }
    
    # Track when we're in an error or failure section
    in_error = False
    in_failure = False
    current_section = []
    current_error = None
    
    # Process the logs line by line
    lines = log_content.split('\n')
    
    for i, line in enumerate(lines):
        # Skip until we find the test session start
        if "test session starts" in line and "===" in line:
            continue
            
        # Check for section markers
        if "==== ERRORS " in line and "====" in line:
            in_error = True
            in_failure = False
            current_section = [line]
            continue
        elif "==== FAILURES " in line and "====" in line:
            in_error = False
            in_failure = True
            current_section = [line]
            continue
        elif "=== short test summary info " in line and "===" in line:
            in_error = False
            in_failure = False
            # Start collecting the summary
            summary_lines = [line]
            # Collect until we hit the end of the summary
            for j in range(i + 1, len(lines)):
                summary_lines.append(lines[j])
                if "===" in lines[j] and "===" in lines[j-1]:
                    break
            results['summary'] = '\n'.join(summary_lines)
            continue
        
        # If we're in an error or failure section, collect the content
        if in_error or in_failure:
            current_section.append(line)
            
            # Check if a new error/failure section is starting
            if ("_____ " in line and line.strip().startswith("_____")) or \
               ("________________" in line and line.strip().startswith("_")):
                # Save the previous section if it exists
                if len(current_section) > 1:
                    if current_error is not None:
                        full_section = current_error + current_section
                        if in_error:
                            results['errors'].append('\n'.join(full_section))
                        else:
                            results['failures'].append('\n'.join(full_section))
                        
                # Start a new section
                current_error = current_section
                current_section = []
            
            # End of a section - save it
            if line.strip() == "" and len(current_section) > 5:
                if current_error is not None:
                    full_section = current_error + current_section
                    if in_error:
                        results['errors'].append('\n'.join(full_section))
                    else:
                        results['failures'].append('\n'.join(full_section))
                    current_error = None
                    current_section = []
    
    # Handle any remaining sections
    if current_error is not None and len(current_section) > 0:
        full_section = current_error + current_section
        if in_error:
            results['errors'].append('\n'.join(full_section))
        elif in_failure:
            results['failures'].append('\n'.join(full_section))
    
    return results


def print_results(results, output_file=None):
    """
    Print parsed results in a readable format
    
    Args:
        results (dict): Dictionary with parsed results
        output_file (file): Optional file handle to write to
    """
    output = []
    
    output.append("=" * 80)
    output.append("SUMMARY")
    output.append("=" * 80)
    if results['summary']:
        output.append(results['summary'])
    output.append("\n")
    
    output.append("=" * 80)
    output.append(f"ERRORS ({len(results['errors'])})")
    output.append("=" * 80)
    
    for i, error in enumerate(results['errors']):
        output.append(f"ERROR {i+1}:")
        output.append("-" * 70)
        output.append(error)
        output.append("\n")
    
    output.append("=" * 80)
    output.append(f"FAILURES ({len(results['failures'])})")
    output.append("=" * 80)
    
    for i, failure in enumerate(results['failures']):
        output.append(f"FAILURE {i+1}:")
        output.append("-" * 70)
        output.append(failure)
        output.append("\n")
    
    output_str = "\n".join(output)
    
    if output_file:
        output_file.write(output_str)
    else:
        print(output_str)


def main():
    parser = argparse.ArgumentParser(
        description='Parse pytest logs and extract failures and errors.')
    parser.add_argument('input_file', nargs='?', 
                      help='Input log file (defaults to stdin if not provided)')
    parser.add_argument('--output', '-o', type=str,
                      help='Output file to write results to (defaults to stdout)')
    
    args = parser.parse_args()
    
    # Read input from file or stdin
    if args.input_file and os.path.exists(args.input_file):
        with open(args.input_file, 'r') as f:
            log_content = f.read()
    else:
        # Check if stdin has content
        if not sys.stdin.isatty():
            log_content = sys.stdin.read()
        else:
            if args.input_file:
                print(f"Error: Input file '{args.input_file}' not found.")
            else:
                print("Error: No input provided. Either specify a file or pipe content to this script.")
            sys.exit(1)
    
    # Parse the logs
    results = parse_test_logs(log_content)
    
    # Output the results
    if args.output:
        with open(args.output, 'w') as f:
            print_results(results, f)
        print(f"Results written to {args.output}")
    else:
        print_results(results)


if __name__ == "__main__":
    main()
