# Debug Session Tracker

The Debug Session Tracker is a tool for tracking, visualizing, and reporting on debugging sessions.

## Overview

When debugging complex issues, it's often difficult to:
- Keep track of all the diagnostics that have been run
- Remember which fixes have been applied and in what order
- Understand the overall debugging journey
- Share debugging knowledge with team members
- Learn patterns from past debugging experiences

The Debug Session Tracker solves these problems by creating a structured approach to debugging that automatically captures the debugging process, visualizes it, and makes it shareable.

## Features

- **Session Management**: Create named debugging sessions, associate them with specific projects, and track session duration and activity.
- **Diagnostic Tracking**: Record diagnostic tools run during a session, store results in structured formats, and track changes in diagnostic results over time.
- **Fix Application Tracking**: Log all fix scripts applied, store before/after states of modified files, and track the effectiveness of each fix.
- **Visualization**: Generate timeline views of the debugging process and visualize the progress with success/failure indicators.
- **Reporting**: Generate markdown/HTML reports of debugging sessions for team sharing and documentation.

## Coming Soon

- **Web Interface**: A browser-based visualization and management interface for debugging sessions is planned for a future release.

## Installation

```bash
# Clone the repository
git clone https://github.com/asabaal/asabaal-utils.git
cd asabaal-utils

# Install the package
pip install -e .
```

## Usage

### Python API

```python
from asabaal_utils.debug_utils import DebugSessionManager

# Create a new debug session
session = DebugSessionManager.create(
    name="Fix forecast display issues",
    project="investing"
)

# Run a diagnostic
diagnostic_results = session.run_diagnostic(
    tool="diagnostic_forecasts.py",
    target="symphony_analyzer.py"
)

# Access diagnostic results
issues = diagnostic_results.issues_found

# Apply a fix
fix_result = session.apply_fix(
    script="fix_forecast_table.py",
    target="report_generator.py"
)

# Mark which issues were resolved
fix_result.mark_resolved(issues[0].id)

# Generate a timeline of the debugging process
timeline = session.generate_timeline()
timeline.save("debug_timeline.html")

# Generate a report of the debugging session
report = session.generate_report(format="markdown")
with open("debug_report.md", "w") as f:
    f.write(report)
```

### Command Line Interface

The Debug Session Tracker includes a command-line interface for managing debugging sessions:

```bash
# Start a new debugging session
asabaal debug start "Fix forecast display issues" --project=investing

# Run a diagnostic
asabaal debug run diagnostic_forecasts.py --target=symphony_analyzer.py

# Apply a fix
asabaal debug fix fix_forecast_table.py --target=report_generator.py

# Mark an issue as resolved
asabaal debug resolve-issue ISSUE_ID --fix=FIX_ID

# View the debugging timeline
asabaal debug visualize timeline --output=debug_timeline.html

# Generate a debugging report
asabaal debug report --format=markdown --output=debug_report.md

# Complete the debugging session
asabaal debug complete --summary="Fixed forecast display issues"
```

## Module Structure

```
debug_utils/
├── session/
│   ├── __init__.py
│   ├── manager.py       # Core session management
│   ├── storage.py       # Session data persistence
│   └── config.py        # Session configuration
├── tracking/
│   ├── __init__.py
│   ├── diagnostics.py   # Track diagnostic runs
│   ├── fixes.py         # Track applied fixes
│   └── changes.py       # Track file changes
├── visualization/
│   ├── __init__.py
│   └── timeline.py      # Timeline generation
└── reporting/
    ├── __init__.py
    ├── markdown.py      # Markdown report generation
    └── html.py          # HTML report generation
```

## Examples

See the `examples/debug_tracker_example.py` file for a complete example of using the Debug Session Tracker.

## Data Storage

By default, debugging sessions are stored in the `~/.asabaal/debug_sessions` directory. Each session is stored as a JSON file with the session ID as the filename.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
