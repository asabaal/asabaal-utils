#!/usr/bin/env python
"""
Example usage of the Debug Session Tracker.

This script demonstrates how to use the Debug Session Tracker to track, visualize,
and report on a debugging session.
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.asabaal_utils.debug_utils import (
    DebugSessionManager,
    DiagnosticRun,
    Issue,
    AppliedFix,
    FileChange
)


def create_sample_file(content):
    """Create a sample file with issues for demonstration purposes.

    Args:
        content: Content to write to the file

    Returns:
        Path to the created file
    """
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        f.write(content.encode('utf-8'))
        return f.name


def create_fix_script(fix_content):
    """Create a sample fix script for demonstration purposes.

    Args:
        fix_content: Content for the fix script

    Returns:
        Path to the created script
    """
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
        f.write("#!/usr/bin/env python\n")
        f.write("import sys\n")
        f.write("\n")
        f.write("def main():\n")
        f.write("    # Get the target file from command-line arguments\n")
        f.write("    if len(sys.argv) < 2:\n")
        f.write("        print('Usage: {} TARGET_FILE'.format(sys.argv[0]))\n")
        f.write("        return 1\n")
        f.write("\n")
        f.write("    target_file = sys.argv[1]\n")
        f.write("\n")
        f.write("    # Read the file content\n")
        f.write("    with open(target_file, 'r') as f:\n")
        f.write("        content = f.read()\n")
        f.write("\n")
        f.write("    # Apply the fix\n")
        f.write(f"    fixed_content = {fix_content}\n")
        f.write("\n")
        f.write("    # Write the fixed content back to the file\n")
        f.write("    with open(target_file, 'w') as f:\n")
        f.write("        f.write(fixed_content)\n")
        f.write("\n")
        f.write("    return 0\n")
        f.write("\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    sys.exit(main())\n")
        
    # Make the script executable
    os.chmod(f.name, 0o755)
    
    return f.name


def main():
    """Main function to demonstrate the Debug Session Tracker."""
    # Create a new debug session
    print("Creating a new debug session...")
    session = DebugSessionManager.create(
        name="Example Debugging Session",
        project="example_project"
    )
    print(f"Session created: {session.id}")
    
    # Create a sample file with issues
    print("\nCreating a sample file with issues...")
    file_content = """import os
import sys

def calculate_sum(numbers):
    # Missing type checking
    result = 0
    for num in numbers:
        result += num
    return result

def process_data(data_file):
    # Missing error handling
    with open(data_file, 'r') as f:
        data = f.readlines()
    
    # Potential issues with string processing
    processed_data = [line.strip.upper() for line in data]
    
    return processed_data

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        process_data(file_path)
    else:
        print("No file specified")
"""
    sample_file = create_sample_file(file_content)
    print(f"Sample file created: {sample_file}")
    
    # Create a manual diagnostic run
    print("\nCreating a diagnostic run...")
    diagnostic = DiagnosticRun(
        id="diag_manual_1",
        session_id=session.id,
        tool="manual_inspection",
        target=sample_file,
        start_time=datetime.now(),
        end_time=datetime.now(),
        parameters={},
        results={},
        issues_found=[]
    )
    
    # Add issues to the diagnostic
    print("Adding issues to the diagnostic...")
    issues = [
        diagnostic.create_issue(
            type="bug",
            severity="high",
            location=f"{sample_file}:15",
            description="AttributeError: No strip method called on string (should be strip())"
        ),
        diagnostic.create_issue(
            type="enhancement",
            severity="medium",
            location=f"{sample_file}:4-7",
            description="Missing type checking for input parameters"
        ),
        diagnostic.create_issue(
            type="bug",
            severity="high",
            location=f"{sample_file}:11-14",
            description="Missing error handling for file operations"
        )
    ]
    
    # Add the diagnostic to the session
    session.add_diagnostic(diagnostic)
    print(f"Added diagnostic with {len(diagnostic.issues_found)} issues")
    
    # Create a fix script for the strip method issue
    print("\nCreating a fix script...")
    fix_script = create_fix_script(
        "content.replace('line.strip.upper()', 'line.strip().upper()')"
    )
    print(f"Fix script created: {fix_script}")
    
    # Create a fix
    print("Applying the fix...")
    
    # First, capture the current state of the file
    with open(sample_file, 'r') as f:
        before_state = f.read()
    
    # Create the fix
    fix = AppliedFix(
        id="fix_1",
        session_id=session.id,
        script=fix_script,
        target=sample_file,
        timestamp=datetime.now(),
        parameters={},
        changes=[],
        resolved_issues=[],
        successful=False
    )
    
    # Run the fix script
    success = fix.run_script(fix_script)
    
    # Read the new state of the file
    with open(sample_file, 'r') as f:
        after_state = f.read()
    
    # Update fix status
    fix.successful = success
    
    # Add the file change to the fix
    if success:
        fix.create_change(
            file_path=sample_file,
            before_state=before_state,
            after_state=after_state
        )
        
        # Mark the issue as resolved by this fix
        issues[0].mark_fixed(fix.id)
        fix.mark_resolved(issues[0].id)
        print("Fix applied successfully and issue marked as resolved")
    else:
        print("Fix application failed")
    
    # Add the fix to the session
    session.add_fix(fix)
    
    # Generate a timeline visualization
    print("\nGenerating timeline visualization...")
    timeline = session.generate_timeline()
    
    # Save the timeline to a file
    timeline_file = os.path.join(tempfile.gettempdir(), "debug_timeline.html")
    timeline.save(timeline_file)
    print(f"Timeline saved to {timeline_file}")
    
    # Generate a report
    print("\nGenerating a report...")
    from src.asabaal_utils.debug_utils import MarkdownReport
    report = MarkdownReport(session)
    
    # Save the report to a file
    report_file = os.path.join(tempfile.gettempdir(), "debug_report.md")
    report.save(report_file)
    print(f"Report saved to {report_file}")
    
    # Complete the session
    print("\nCompleting the debug session...")
    DebugSessionManager.complete_session(
        session.id,
        summary="Example debugging session demonstrating the Debug Session Tracker"
    )
    print("Session completed")
    
    # Clean up the sample files
    print("\nCleaning up sample files...")
    os.unlink(sample_file)
    os.unlink(fix_script)
    print("Done")
    
    print("\nExample complete!")
    print(f"You can view the timeline at: file://{timeline_file}")
    print(f"You can view the report at: file://{report_file}")


if __name__ == '__main__':
    main()
