"""Command-line interface for Debug Session Tracker.

This module provides a command-line interface for the Debug Session Tracker,
allowing users to create, manage, and analyze debug sessions from the command line.
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

from .session.manager import DebugSessionManager
from .tracking.diagnostics import PythonLintDiagnostic
from .visualization.timeline import Timeline
from .reporting.markdown import MarkdownReport
from .reporting.html import HTMLReport


def parse_args():
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Debug Session Tracker CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start a new debugging session
  asabaal debug start "Fix forecast display issues" --project=investing
  
  # Run a diagnostic
  asabaal debug run diagnostic_forecasts.py --target=symphony_analyzer.py
  
  # Apply a fix
  asabaal debug fix fix_forecast_table.py --target=report_generator.py
  
  # Mark an issue as resolved
  asabaal debug resolve-issue ISSUE_ID
  
  # View the debugging timeline
  asabaal debug visualize timeline
  
  # Generate a debugging report
  asabaal debug report --format=markdown --output=debug_report.md
  
  # Complete the debugging session
  asabaal debug complete --summary="Fixed forecast display issues"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Command to execute')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a new debugging session')
    start_parser.add_argument('name', help='User-friendly session name')
    start_parser.add_argument('--project', '-p', required=True, help='Associated project/repository')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List debugging sessions')
    list_parser.add_argument('--status', '-s', choices=['active', 'completed', 'abandoned'], help='Filter by session status')
    list_parser.add_argument('--project', '-p', help='Filter by project')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a diagnostic')
    run_parser.add_argument('tool', help='Diagnostic tool to run')
    run_parser.add_argument('--target', '-t', required=True, help='File/module to diagnose')
    run_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    run_parser.add_argument('--param', '-P', action='append', nargs=2, metavar=('KEY', 'VALUE'), help='Tool-specific parameters')
    
    # Fix command
    fix_parser = subparsers.add_parser('fix', help='Apply a fix')
    fix_parser.add_argument('script', help='Fix script to run')
    fix_parser.add_argument('--target', '-t', required=True, help='File/module to fix')
    fix_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    fix_parser.add_argument('--param', '-P', action='append', nargs=2, metavar=('KEY', 'VALUE'), help='Fix-specific parameters')
    
    # Resolve command
    resolve_parser = subparsers.add_parser('resolve-issue', help='Mark an issue as resolved')
    resolve_parser.add_argument('issue_id', help='Issue ID to mark as resolved')
    resolve_parser.add_argument('--fix', '-f', required=True, help='Fix ID that resolved the issue')
    resolve_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    
    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', help='Visualize a debugging session')
    visualize_parser.add_argument('type', choices=['timeline'], help='Visualization type')
    visualize_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    visualize_parser.add_argument('--output', '-o', help='Output file path')
    visualize_parser.add_argument('--format', '-f', choices=['json', 'html'], default='html', help='Output format')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate a report')
    report_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    report_parser.add_argument('--format', '-f', choices=['markdown', 'html'], default='markdown', help='Report format')
    report_parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Complete a debugging session')
    complete_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    complete_parser.add_argument('--summary', help='Summary of the debugging session')
    
    # Abandon command
    abandon_parser = subparsers.add_parser('abandon', help='Abandon a debugging session')
    abandon_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    abandon_parser.add_argument('--reason', '-r', help='Reason for abandoning the session')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show details of a debugging session')
    show_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export a debugging session')
    export_parser.add_argument('--session', '-s', help='Session ID (defaults to current session)')
    export_parser.add_argument('--output', '-o', required=True, help='Output directory')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import a debugging session')
    import_parser.add_argument('input', help='Input directory or file')
    
    return parser.parse_args()


def get_current_session_id():
    """Get the ID of the current debugging session.

    Returns:
        Current session ID, or None if no current session
    """
    # Check if there's a current session file
    home_dir = os.path.expanduser("~")
    current_session_file = os.path.join(home_dir, ".asabaal", "current_debug_session")
    
    if os.path.exists(current_session_file):
        try:
            with open(current_session_file, 'r') as f:
                return f.read().strip()
        except:
            return None
            
    return None


def set_current_session_id(session_id):
    """Set the ID of the current debugging session.

    Args:
        session_id: Session ID to set as current
    """
    # Create the .asabaal directory if it doesn't exist
    home_dir = os.path.expanduser("~")
    asabaal_dir = os.path.join(home_dir, ".asabaal")
    os.makedirs(asabaal_dir, exist_ok=True)
    
    # Write the current session ID to a file
    current_session_file = os.path.join(asabaal_dir, "current_debug_session")
    
    with open(current_session_file, 'w') as f:
        f.write(session_id)


def get_session(args):
    """Get a debugging session based on command-line arguments.

    Args:
        args: Command-line arguments

    Returns:
        The requested debugging session

    Raises:
        ValueError: If no session is specified and there's no current session
    """
    # Get the session ID from arguments or current session
    session_id = getattr(args, 'session', None) or get_current_session_id()
    
    if not session_id:
        raise ValueError("No session specified. Please specify a session ID or start a new session.")
        
    # Get the session
    session = DebugSessionManager.get_session(session_id)
    
    if not session:
        raise ValueError(f"Session not found: {session_id}")
        
    return session


def command_start(args):
    """Handle the 'start' command.

    Args:
        args: Command-line arguments
    """
    # Create a new session
    session = DebugSessionManager.create(name=args.name, project=args.project)
    
    # Set as current session
    set_current_session_id(session.id)
    
    print(f"Started new debugging session: {session.name} ({session.id})")
    print(f"Project: {session.project}")


def command_list(args):
    """Handle the 'list' command.

    Args:
        args: Command-line arguments
    """
    # Get sessions based on filters
    if args.status:
        sessions = DebugSessionManager.get_storage()._storage.list_sessions(status=args.status)
    else:
        sessions = DebugSessionManager.get_all_sessions()
        
    # Filter by project if specified
    if args.project:
        sessions = [s for s in sessions if s.project == args.project]
        
    # Sort sessions by creation time (newest first)
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    
    if not sessions:
        print("No debugging sessions found.")
        return
        
    # Get the current session ID
    current_session_id = get_current_session_id()
    
    # Print sessions
    print(f"Found {len(sessions)} debugging sessions:")
    print("\n{:<36} {:<20} {:<15} {:<20} {:<20}".format("ID", "Name", "Status", "Project", "Created"))
    print("-" * 100)
    
    for session in sessions:
        # Mark the current session with an asterisk
        current_marker = "*" if session.id == current_session_id else " "
        
        created_str = session.created_at.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_marker} {session.id:<35} {session.name:<20} {session.status:<15} {session.project:<20} {created_str}")


def command_run(args):
    """Handle the 'run' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Parse parameters
    parameters = {}
    if args.param:
        for key, value in args.param:
            parameters[key] = value
    
    # Run the diagnostic
    print(f"Running diagnostic: {args.tool} on {args.target}")
    
    diagnostic = session.run_diagnostic(
        tool=args.tool,
        target=args.target,
        parameters=parameters
    )
    
    # Print diagnostic results
    print(f"Diagnostic completed in {diagnostic.duration():.2f} seconds")
    print(f"Issues found: {len(diagnostic.issues_found)}")
    
    issue_counts = diagnostic.count_issues_by_severity()
    for severity, count in issue_counts.items():
        if count > 0:
            print(f"  {severity.capitalize()}: {count}")
            
    # Save the session
    DebugSessionManager.update_session(session)


def command_fix(args):
    """Handle the 'fix' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Parse parameters
    parameters = {}
    if args.param:
        for key, value in args.param:
            parameters[key] = value
    
    # Apply the fix
    print(f"Applying fix: {args.script} on {args.target}")
    
    fix = session.apply_fix(
        script=args.script,
        target=args.target,
        parameters=parameters
    )
    
    # Print fix results
    status = "Successful" if fix.successful else "Failed"
    print(f"Fix application {status}")
    print(f"Changes: {len(fix.changes)}")
    
    # Save the session
    DebugSessionManager.update_session(session)


def command_resolve_issue(args):
    """Handle the 'resolve-issue' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Find the issue
    issue = None
    for diagnostic in session.diagnostics:
        for i in diagnostic.issues_found:
            if i.id == args.issue_id:
                issue = i
                break
        if issue:
            break
            
    if not issue:
        print(f"Issue not found: {args.issue_id}")
        return
        
    # Find the fix
    fix = None
    for f in session.fixes:
        if f.id == args.fix:
            fix = f
            break
            
    if not fix:
        print(f"Fix not found: {args.fix}")
        return
        
    # Mark the issue as resolved
    issue.mark_fixed(fix.id)
    fix.mark_resolved(issue.id)
    
    print(f"Marked issue {args.issue_id} as resolved by fix {args.fix}")
    
    # Save the session
    DebugSessionManager.update_session(session)


def command_visualize(args):
    """Handle the 'visualize' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    if args.type == 'timeline':
        # Generate timeline
        timeline = session.generate_timeline()
        
        # Save timeline if output specified
        if args.output:
            if args.format == 'json':
                with open(args.output, 'w') as f:
                    f.write(timeline.to_json())
            else:  # html
                with open(args.output, 'w') as f:
                    f.write(timeline.to_html())
                    
            print(f"Timeline saved to {args.output}")
        else:
            # Print timeline summary
            print(f"Timeline for session: {session.name} ({session.id})")
            print(f"Events: {len(timeline.events)}")
            print("Use --output to save the timeline to a file")


def command_report(args):
    """Handle the 'report' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    print(f"Generating {args.format} report for session: {session.name} ({session.id})")
    
    # Generate report
    if args.format == 'markdown':
        report = MarkdownReport(session)
    else:  # html
        report = HTMLReport(session)
        
    # Save report
    report.save(args.output)
    
    print(f"Report saved to {args.output}")


def command_complete(args):
    """Handle the 'complete' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Complete the session
    DebugSessionManager.complete_session(session.id, args.summary)
    
    print(f"Completed debugging session: {session.name} ({session.id})")
    if args.summary:
        print(f"Summary: {args.summary}")
        
    # Clear current session if this is the current session
    current_session_id = get_current_session_id()
    if current_session_id == session.id:
        set_current_session_id("")


def command_abandon(args):
    """Handle the 'abandon' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Abandon the session
    DebugSessionManager.abandon_session(session.id, args.reason)
    
    print(f"Abandoned debugging session: {session.name} ({session.id})")
    if args.reason:
        print(f"Reason: {args.reason}")
        
    # Clear current session if this is the current session
    current_session_id = get_current_session_id()
    if current_session_id == session.id:
        set_current_session_id("")


def command_show(args):
    """Handle the 'show' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Print session details
    print(f"Debugging Session: {session.name} ({session.id})")
    print(f"Project: {session.project}")
    print(f"Status: {session.status}")
    print(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Last Updated: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print diagnostics
    print(f"\nDiagnostics: {len(session.diagnostics)}")
    for i, diagnostic in enumerate(session.diagnostics):
        print(f"  {i+1}. {diagnostic.tool} on {diagnostic.target}")
        print(f"     Issues: {len(diagnostic.issues_found)}")
        
    # Print fixes
    print(f"\nFixes: {len(session.fixes)}")
    for i, fix in enumerate(session.fixes):
        status = "Successful" if fix.successful else "Failed"
        print(f"  {i+1}. {fix.script} on {fix.target} ({status})")
        print(f"     Changes: {len(fix.changes)}")
        print(f"     Issues Resolved: {len(fix.resolved_issues)}")


def command_export(args):
    """Handle the 'export' command.

    Args:
        args: Command-line arguments
    """
    # Get the session
    session = get_session(args)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Export the session
    # We're using a simplified approach here - just exporting the session JSON
    # A real implementation would export diagnostics, fixes, etc.
    session_file = os.path.join(args.output, f"{session.id}.json")
    with open(session_file, 'w') as f:
        import json
        f.write(json.dumps(session.to_dict(), indent=2))
        
    print(f"Exported session {session.id} to {session_file}")


def command_import(args):
    """Handle the 'import' command.

    Args:
        args: Command-line arguments
    """
    # Check if input is a file or directory
    if os.path.isfile(args.input):
        # Import a single session file
        try:
            with open(args.input, 'r') as f:
                import json
                session_dict = json.load(f)
                
            # Create a session from the dictionary
            from .session.session import DebugSession
            session = DebugSession.from_dict(session_dict)
            
            # Save the session
            DebugSessionManager.update_session(session)
            
            print(f"Imported session: {session.name} ({session.id})")
        except Exception as e:
            print(f"Error importing session from {args.input}: {e}")
    else:
        # Import all session files in the directory
        if not os.path.isdir(args.input):
            print(f"Input is not a file or directory: {args.input}")
            return
            
        # Find all JSON files in the directory
        import glob
        session_files = glob.glob(os.path.join(args.input, "*.json"))
        
        if not session_files:
            print(f"No session files found in {args.input}")
            return
            
        # Import each session file
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    import json
                    session_dict = json.load(f)
                    
                # Create a session from the dictionary
                from .session.session import DebugSession
                session = DebugSession.from_dict(session_dict)
                
                # Save the session
                DebugSessionManager.update_session(session)
                
                print(f"Imported session: {session.name} ({session.id})")
            except Exception as e:
                print(f"Error importing session from {session_file}: {e}")


def main():
    """Main entry point for the Debug Session Tracker CLI."""
    # Parse command-line arguments
    args = parse_args()
    
    try:
        # Dispatch to the appropriate command handler
        if args.command == 'start':
            command_start(args)
        elif args.command == 'list':
            command_list(args)
        elif args.command == 'run':
            command_run(args)
        elif args.command == 'fix':
            command_fix(args)
        elif args.command == 'resolve-issue':
            command_resolve_issue(args)
        elif args.command == 'visualize':
            command_visualize(args)
        elif args.command == 'report':
            command_report(args)
        elif args.command == 'complete':
            command_complete(args)
        elif args.command == 'abandon':
            command_abandon(args)
        elif args.command == 'show':
            command_show(args)
        elif args.command == 'export':
            command_export(args)
        elif args.command == 'import':
            command_import(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
