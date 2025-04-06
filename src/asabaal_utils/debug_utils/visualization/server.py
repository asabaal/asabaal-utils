"""Simple HTTP server for visualizing debug sessions.

This module provides a simple HTTP server that can be used to visualize
debug sessions in a web browser.
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import tempfile

from ..session.manager import DebugSessionManager
from .timeline import Timeline


class DebugVisualizationHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for debug visualizations."""

    def __init__(self, *args, **kwargs):
        self.sessions_dir = kwargs.pop('sessions_dir', None)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self._generate_index_page().encode())
        elif self.path == '/sessions':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self._get_sessions()).encode())
        elif self.path.startswith('/timeline/'):
            session_id = self.path.split('/')[-1]
            timeline_html = self._generate_timeline(session_id)
            if timeline_html:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(timeline_html.encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Session not found')
        else:
            super().do_GET()

    def _generate_index_page(self) -> str:
        """Generate the index page listing all sessions.

        Returns:
            HTML content for the index page
        """
        sessions = self._get_sessions()
        
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debug Session Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1, h2 {
            color: #2c3e50;
        }
        .session-list {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .session-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            width: 300px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .session-card h3 {
            margin-top: 0;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .session-card p {
            margin: 5px 0;
        }
        .session-card a {
            display: inline-block;
            margin-top: 10px;
            padding: 5px 10px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 3px;
        }
        .session-card a:hover {
            background-color: #2980b9;
        }
        .status-active {
            color: #2ecc71;
            font-weight: bold;
        }
        .status-completed {
            color: #3498db;
            font-weight: bold;
        }
        .status-abandoned {
            color: #e74c3c;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Debug Session Tracker</h1>
    <p>Select a session to view its timeline:</p>
    
    <div class="session-list">
"""
        
        for session in sessions:
            status_class = f"status-{session['status']}"
            html += f"""
        <div class="session-card">
            <h3>{session['name']}</h3>
            <p><strong>ID:</strong> {session['id']}</p>
            <p><strong>Project:</strong> {session['project']}</p>
            <p><strong>Status:</strong> <span class="{status_class}">{session['status'].capitalize()}</span></p>
            <p><strong>Created:</strong> {session['created_at']}</p>
            <p><strong>Diagnostics:</strong> {len(session.get('diagnostics', []))}</p>
            <p><strong>Fixes:</strong> {len(session.get('fixes', []))}</p>
            <a href="/timeline/{session['id']}">View Timeline</a>
        </div>
"""
            
        html += """
    </div>
    
    <script>
        // Auto-refresh the page every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""
        
        return html

    def _get_sessions(self) -> List[Dict[str, Any]]:
        """Get all debug sessions.

        Returns:
            List of session dictionaries
        """
        # Get all sessions from the manager
        sessions = DebugSessionManager.get_all_sessions()
        
        # Convert to dictionaries
        return [session.to_dict() for session in sessions]

    def _generate_timeline(self, session_id: str) -> Optional[str]:
        """Generate a timeline visualization for a session.

        Args:
            session_id: ID of the session to visualize

        Returns:
            HTML content for the timeline, or None if session not found
        """
        # Get the session
        session = DebugSessionManager.get_session(session_id)
        if not session:
            return None
            
        # Generate timeline
        timeline = Timeline(session)
        
        # Get the HTML
        return timeline.to_html()


def start_server(port: int = 8000, open_browser: bool = True):
    """Start the debug visualization server.

    Args:
        port: Port to listen on
        open_browser: Whether to open a browser window
    """
    # Get the directory for session storage
    home_dir = os.path.expanduser("~")
    sessions_dir = os.path.join(home_dir, ".asabaal", "debug_sessions")
    
    # Create a request handler with the sessions directory
    handler = lambda *args, **kwargs: DebugVisualizationHandler(*args, sessions_dir=sessions_dir, **kwargs)
    
    # Start the server
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Debug visualization server running at http://localhost:{port}")
        
        # Open a browser window
        if open_browser:
            webbrowser.open(f"http://localhost:{port}")
            
        # Serve until interrupted
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
            httpd.server_close()


if __name__ == "__main__":
    # Start the server
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port=port)
