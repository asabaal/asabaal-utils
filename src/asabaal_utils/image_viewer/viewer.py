import os
import sys
import json
import signal
import subprocess
import webbrowser
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import atexit

class ImageViewer:
    def __init__(self, port=3000):
        self.port = port
        self.server_process = None
        self.node_process = None
        self.image_viewer_dir = Path(__file__).parent.parent / 'image_viewer'
        
    def _setup_temp_config(self, images):
        """Create temporary configuration with image paths"""
        config = {
            'images': [
                {'src': f'file://{str(Path(img).absolute())}', 'alt': Path(img).name}
                for img in images
            ]
        }
        
        config_path = self.image_viewer_dir / 'web_app' / 'public' / 'config.json'
        # Ensure the directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f)

    def _start_dev_server(self):
        """Start the Vite development server"""
        os.chdir(self.image_viewer_dir / 'web_app')
        
        # Add debug logging
        print("Starting dev server in:", os.getcwd())
        
        # Install dependencies if needed
        if not (Path.cwd() / 'node_modules').exists():
            print("Installing dependencies...")
            subprocess.run(['npm', 'install'], check=True)
        
        print(f"Starting Vite server on port {self.port}")
        self.node_process = subprocess.Popen(
            ['npm', 'run', 'dev', '--', '--port', str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # Add some startup delay and logging
    time.sleep(3)  # Give more time for the server to start
    print(f"Server should be running at http://localhost:{self.port}")

    def _cleanup(self):
        """Cleanup processes on exit"""
        if self.node_process:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.node_process.pid)])
            else:
                os.killpg(os.getpgid(self.node_process.pid), signal.SIGTERM)

    def view_images(self, images):
        """
        Launch the image viewer with specified images
        
        Args:
            images: List of paths to image files
        """
        try:
            # Setup configuration with image paths
            self._setup_temp_config(images)
            
            # Start the development server
            self._start_dev_server()
            
            # Register cleanup
            atexit.register(self._cleanup)
            
            # Open browser
            webbrowser.open(f'http://localhost:{self.port}')
            
            print(f"Image viewer running at http://localhost:{self.port}")
            print("Press Ctrl+C to exit")
            
            # Keep the server running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down image viewer...")
                
        finally:
            self._cleanup()

def view_images(images):
    """
    Convenience function to view images
    
    Args:
        images: List of paths to image files
    """
    viewer = ImageViewer()
    viewer.view_images(images)