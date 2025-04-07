"""Timeline visualization for Debug Session Tracker.

This module provides the Timeline class for visualizing the debugging process
as a chronological timeline.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from ..session.session import DebugSession


class Timeline:
    """Timeline visualization of a debugging session.

    This class generates a timeline visualization of a debugging session,
    showing diagnostics and fixes in chronological order.

    Attributes:
        session: The debug session to visualize
        events: List of timeline events
    """

    def __init__(self, session: DebugSession):
        """Initialize the timeline visualization.

        Args:
            session: The debug session to visualize
        """
        self.session = session
        self.events = self._build_events()

    def _build_events(self) -> List[Dict[str, Any]]:
        """Build a list of timeline events from the session.

        Returns:
            List of timeline events
        """
        events = []
        
        # Add session creation event
        events.append({
            "type": "session_start",
            "timestamp": self.session.created_at,
            "title": f"Session Created: {self.session.name}",
            "details": {
                "session_id": self.session.id,
                "project": self.session.project
            }
        })
        
        # Add diagnostic events
        for diagnostic in self.session.diagnostics:
            events.append({
                "type": "diagnostic",
                "timestamp": diagnostic.start_time,
                "title": f"Diagnostic: {diagnostic.tool}",
                "details": {
                    "id": diagnostic.id,
                    "tool": diagnostic.tool,
                    "target": diagnostic.target,
                    "duration": diagnostic.duration(),
                    "issue_count": len(diagnostic.issues_found),
                    "issue_severity": diagnostic.count_issues_by_severity()
                }
            })
        
        # Add fix events
        for fix in self.session.fixes:
            events.append({
                "type": "fix",
                "timestamp": fix.timestamp,
                "title": f"Fix Applied: {fix.script}",
                "details": {
                    "id": fix.id,
                    "script": fix.script,
                    "target": fix.target,
                    "successful": fix.successful,
                    "issues_resolved": len(fix.resolved_issues),
                    "changes": [c.summarize_changes() for c in fix.changes]
                }
            })
            
        # Add session completion event if the session is completed
        if self.session.status == "completed":
            events.append({
                "type": "session_end",
                "timestamp": self.session.updated_at,
                "title": "Session Completed",
                "details": {
                    "duration": (self.session.updated_at - self.session.created_at).total_seconds(),
                    "summary": self.session.summary or "No summary provided"
                }
            })
            
        # Add session abandonment event if the session was abandoned
        elif self.session.status == "abandoned":
            events.append({
                "type": "session_abandoned",
                "timestamp": self.session.updated_at,
                "title": "Session Abandoned",
                "details": {
                    "duration": (self.session.updated_at - self.session.created_at).total_seconds(),
                    "reason": self.session.abandonment_reason or "No reason provided"
                }
            })
            
        # Sort events by timestamp
        events.sort(key=lambda e: e["timestamp"])
        
        return events

    def to_dict(self) -> Dict[str, Any]:
        """Convert the timeline to a dictionary.

        Returns:
            Dictionary representation of the timeline
        """
        # Convert events to a serializable format
        serializable_events = []
        for event in self.events:
            event_copy = event.copy()
            event_copy["timestamp"] = event_copy["timestamp"].isoformat()
            serializable_events.append(event_copy)
            
        return {
            "session_id": self.session.id,
            "session_name": self.session.name,
            "project": self.session.project,
            "events": serializable_events
        }

    def to_json(self) -> str:
        """Convert the timeline to a JSON string.

        Returns:
            JSON representation of the timeline
        """
        return json.dumps(self.to_dict(), indent=2)

    def save(self, file_path: str) -> bool:
        """Save the timeline to a file.

        Args:
            file_path: Path where the timeline will be saved

        Returns:
            True if the timeline was saved successfully, False otherwise
        """
        try:
            # Determine the file format based on extension
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.json':
                # Save as JSON
                with open(file_path, 'w') as f:
                    f.write(self.to_json())
            elif ext.lower() == '.html':
                # Save as HTML
                with open(file_path, 'w') as f:
                    f.write(self.to_html())
            else:
                # Default to JSON
                with open(file_path, 'w') as f:
                    f.write(self.to_json())
                    
            return True
        except Exception as e:
            print(f"Error saving timeline: {e}")
            return False

    def to_html(self) -> str:
        """Convert the timeline to an HTML visualization.

        Returns:
            HTML representation of the timeline
        """
        # Build HTML representation of the timeline
        html = ['<!DOCTYPE html>',
                '<html>',
                '<head>',
                '  <title>Debug Session Timeline</title>',
                '  <style>',
                '    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }',
                '    h1 { color: #333; }',
                '    .timeline { position: relative; max-width: 1200px; margin: 0 auto; }',
                '    .timeline::after { content: ""; position: absolute; width: 6px; background-color: #2196F3; top: 0; bottom: 0; left: 50%; margin-left: -3px; }',
                '    .event { position: relative; width: 50%; padding: 10px 40px; }',
                '    .event-left { left: 0; }',
                '    .event-right { left: 50%; }',
                '    .event-content { padding: 20px; background-color: white; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }',
                '    .event-content h2 { margin-top: 0; color: #333; }',
                '    .event-content p { margin: 5px 0; }',
                '    .event::after { content: ""; position: absolute; width: 20px; height: 20px; background-color: #fff; border: 4px solid #FF9800; border-radius: 50%; top: 15px; z-index: 1; }',
                '    .event-left::after { right: -13px; }',
                '    .event-right::after { left: -13px; }',
                '    .session-start::after { border-color: #4CAF50; }',
                '    .session-end::after, .session-abandoned::after { border-color: #F44336; }',
                '    .diagnostic::after { border-color: #2196F3; }',
                '    .fix::after { border-color: #FF9800; }',
                '    .fix-success::after { border-color: #4CAF50; }',
                '    .fix-failure::after { border-color: #F44336; }',
                '    .timestamp { color: #999; font-size: 0.8em; }',
                '  </style>',
                '</head>',
                '<body>',
                f'  <h1>Debug Session Timeline: {self.session.name}</h1>',
                f'  <p>Project: {self.session.project}</p>',
                f'  <p>Status: {self.session.status}</p>',
                '  <div class="timeline">']
        
        # Add events to the timeline
        for i, event in enumerate(self.events):
            # Determine if event should be on left or right side
            side = "event-left" if i % 2 == 0 else "event-right"
            
            # Format timestamp
            timestamp = event["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            
            # Format event content based on type
            content = ['    <div class="event-content">',
                       f'      <h2>{event["title"]}</h2>',
                       f'      <p class="timestamp">{timestamp}</p>']
            
            if event["type"] == "diagnostic":
                details = event["details"]
                content.extend([
                    f'      <p>Tool: {details["tool"]}</p>',
                    f'      <p>Target: {details["target"]}</p>',
                    f'      <p>Issues Found: {details["issue_count"]}</p>',
                    '      <p>Severity:</p>',
                    '      <ul>'
                ])
                
                for severity, count in details["issue_severity"].items():
                    if count > 0:
                        content.append(f'        <li>{severity}: {count}</li>')
                        
                content.append('      </ul>')
                
            elif event["type"] == "fix":
                details = event["details"]
                content.extend([
                    f'      <p>Script: {details["script"]}</p>',
                    f'      <p>Target: {details["target"]}</p>',
                    f'      <p>Status: {"Successful" if details["successful"] else "Failed"}</p>',
                    f'      <p>Issues Resolved: {details["issues_resolved"]}</p>'
                ])
                
                if details["changes"]:
                    content.append('      <p>Changes:</p>')
                    content.append('      <ul>')
                    
                    for change in details["changes"]:
                        content.append(f'        <li>{change["file_path"]} ({change["lines_added"]} added, {change["lines_removed"]} removed)</li>')
                        
                    content.append('      </ul>')
            
            elif event["type"] in ["session_end", "session_abandoned"]:
                details = event["details"]
                
                # Format duration
                duration_seconds = details["duration"]
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                
                content.extend([
                    f'      <p>Duration: {duration_str}</p>',
                    f'      <p>{details["summary"] if "summary" in details else details["reason"]}</p>'
                ])
                
            content.append('    </div>')
            
            # Additional classes based on event type
            event_classes = f"event {side} {event['type']}"
            if event["type"] == "fix":
                event_classes += " fix-success" if event["details"]["successful"] else " fix-failure"
                
            # Add the event to the timeline
            html.append(f'    <div class="{event_classes}">')
            html.extend(content)
            html.append('    </div>')
        
        # Close the HTML
        html.extend(['  </div>',
                     '</body>',
                     '</html>'])
        
        return '\n'.join(html)
