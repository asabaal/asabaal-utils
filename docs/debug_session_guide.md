# Debug Session Tracker - Practical Guide

This guide provides practical instructions for using the Debug Session Tracker during debugging sessions.

## Overview

The Debug Session Tracker helps manage debugging sessions by:
- Tracking diagnostics and issues found
- Recording applied fixes and their effects
- Visualizing the debugging process
- Generating comprehensive reports

## Typical Debugging Workflow

1. **Start a debugging session** when an issue is identified
2. **Run diagnostics** to identify specific problems
3. **Apply fixes** to address the issues
4. **Verify fixes** worked as expected
5. **Document the process** for future reference
6. **Complete the session** with a summary

## Using the Debug Session Tracker in a Collaborative Setting

When working with an AI assistant or team member, this tool provides a structured way to track progress and share knowledge about debugging efforts.

### Step 1: Initialize a Debugging Session

When you encounter a bug or issue that needs debugging, start by creating a new debugging session:

```python
from asabaal_utils.debug_utils import DebugSessionManager

# Create a new debug session
session = DebugSessionManager.create(
    name="Fix [brief description of the issue]",
    project="[project name]"
)
print(f"Created debug session: {session.id}")
```

Or via the command line:

```bash
python -m asabaal_utils.debug_utils start "Fix [brief description of the issue]" --project="[project name]"
```

### Step 2: Run Diagnostics

Once the session is initialized, run diagnostics to identify the issues:

```python
# Run a diagnostic
diagnostic = session.run_diagnostic(
    tool="[diagnostic tool/script]",
    target="[file/module with issues]"
)

# Manually add issues if not automatically detected
diagnostic.create_issue(
    type="bug",  # Or "enhancement", "performance", etc.
    severity="high",  # Options: "critical", "high", "medium", "low"
    location="[file]:[line number]",
    description="[detailed description of the issue]"
)

# Save the session
DebugSessionManager.update_session(session)
```

Or via the command line:

```bash
# Run a diagnostic tool
python -m asabaal_utils.debug_utils run [diagnostic-tool] --target=[file/module]
```

### Step 3: Create and Apply Fixes

Create fix scripts that address the identified issues:

```python
# Example fix script structure (save as fix_script.py)
#!/usr/bin/env python
import sys

def main():
    if len(sys.argv) < 2:
        print('Usage: {} TARGET_FILE'.format(sys.argv[0]))
        return 1

    target_file = sys.argv[1]

    # Read the file content
    with open(target_file, 'r') as f:
        content = f.read()

    # Apply the fix - this is where you make your changes
    fixed_content = content.replace(
        '[problematic code]', 
        '[fixed code]'
    )

    # Write the fixed content back to the file
    with open(target_file, 'w') as f:
        f.write(fixed_content)

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

Apply the fix:

```python
# Apply the fix
fix = session.apply_fix(
    script="./fix_script.py",
    target="[file to fix]"
)

# Mark which issues were resolved by this fix
fix.mark_resolved("[issue-id]")

# Save the session
DebugSessionManager.update_session(session)
```

Or via the command line:

```bash
# Apply a fix
python -m asabaal_utils.debug_utils fix ./fix_script.py --target=[file to fix]

# Mark an issue as resolved
python -m asabaal_utils.debug_utils resolve-issue [issue-id] --fix=[fix-id]
```

### Step 4: Generate Visualizations and Reports

Once you've applied fixes, generate visualizations and reports to document the debugging process:

```python
# Generate a timeline visualization
timeline = session.generate_timeline()
timeline.save("debug_timeline.html")

# Generate a report
report = session.generate_report(format="markdown")
with open("debug_report.md", "w") as f:
    f.write(report)
```

Or via the command line:

```bash
# Generate a timeline visualization
python -m asabaal_utils.debug_utils visualize timeline --output=debug_timeline.html

# Generate a report
python -m asabaal_utils.debug_utils report --format=markdown --output=debug_report.md
```

### Step 5: Complete the Debugging Session

Once all issues are resolved, complete the debugging session:

```python
# Complete the session
DebugSessionManager.complete_session(
    session.id,
    summary="Fixed [brief description of what was fixed and how]"
)
```

Or via the command line:

```bash
# Complete the debugging session
python -m asabaal_utils.debug_utils complete --summary="Fixed [brief description of what was fixed and how]"
```

## Practical Example: Using the Debug Session Tracker with an AI Assistant

Here's how a typical interaction might look when debugging with an AI assistant:

1. **Identify an issue** and describe it to the AI assistant

2. **Ask the AI assistant to help set up a debug session**:
   ```
   Could you help me set up a debugging session for this issue?
   ```

3. **The AI provides code to initialize a session**:
   ```python
   from asabaal_utils.debug_utils import DebugSessionManager
   
   session = DebugSessionManager.create(
       name="Fix data processing error in analytics module",
       project="data_pipeline"
   )
   print(f"Created debug session: {session.id}")
   ```

4. **Share error logs or symptoms with the AI**

5. **The AI suggests diagnostic approaches**:
   ```python
   # Run a diagnostic on the problematic file
   diagnostic = session.run_diagnostic(
       tool="manual_inspection",
       target="analytics/processor.py"
   )
   
   # Add the issues found
   diagnostic.create_issue(
       type="bug",
       severity="high",
       location="analytics/processor.py:156",
       description="IndexError when processing empty dataframes"
   )
   
   # Save the session
   DebugSessionManager.update_session(session)
   ```

6. **The AI suggests a fix**:
   ```python
   # Create a fix script (save as fix_empty_df.py)
   #!/usr/bin/env python
   import sys
   
   def main():
       target_file = sys.argv[1]
       
       with open(target_file, 'r') as f:
           content = f.read()
           
       # Fix the issue by adding a check for empty dataframes
       fixed_content = content.replace(
           "def process_dataframe(df):",
           "def process_dataframe(df):\n    if df.empty:\n        return df"
       )
       
       with open(target_file, 'w') as f:
           f.write(fixed_content)
           
       return 0
       
   if __name__ == '__main__':
       sys.exit(main())
   ```

7. **Apply the fix and mark the issue as resolved**:
   ```python
   # Apply the fix
   fix = session.apply_fix(
       script="./fix_empty_df.py",
       target="analytics/processor.py"
   )
   
   # Mark the issue as resolved
   fix.mark_resolved("issue_1_test_diagnostic")
   
   # Save the session
   DebugSessionManager.update_session(session)
   ```

8. **Generate a report for documentation**:
   ```python
   # Generate a report
   report = session.generate_report(format="markdown")
   with open("empty_dataframe_fix_report.md", "w") as f:
       f.write(report)
   ```

9. **Complete the debugging session**:
   ```python
   # Complete the session
   DebugSessionManager.complete_session(
       session.id,
       summary="Fixed IndexError in analytics processor by adding empty dataframe check"
   )
   ```

## Tips for Effective Debugging Sessions

1. **Be descriptive** in session names and issue descriptions
2. **Create small, focused fix scripts** that address one issue at a time
3. **Add detailed information** to diagnostic issues
4. **Generate reports** after significant debugging milestones
5. **Use the timeline visualization** to understand the debugging journey
6. **Keep track of session IDs** when working on multiple issues

## Common Debugging Patterns

### Pattern 1: Investigate → Fix → Verify
For straightforward bugs with clear causes:
1. Run diagnostics to identify the issue
2. Create a fix script
3. Apply the fix and verify it resolves the issue

### Pattern 2: Iterative Exploration
For complex bugs with unclear causes:
1. Run initial diagnostics
2. Create exploratory fix scripts
3. Apply fixes and observe results
4. Run additional diagnostics
5. Refine fixes based on new information

### Pattern 3: Multi-Issue Resolution
For addressing multiple related issues:
1. Run diagnostics to identify all related issues
2. Prioritize issues by severity
3. Create fix scripts for each issue
4. Apply fixes in order of priority
5. Verify each fix resolves its targeted issue

## Conclusion

The Debug Session Tracker provides a structured approach to debugging that helps document the debugging process, track applied fixes, and share knowledge with team members. By following the patterns and examples in this guide, you can make your debugging sessions more efficient and productive.
