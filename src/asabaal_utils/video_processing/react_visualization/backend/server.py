#!/usr/bin/env python3
"""
Backend server for the CapCut Project Visualizer.

This Flask-based server provides API endpoints to analyze CapCut projects and serve
the React frontend. It bridges the Python analysis tools with the React visualization.
"""

import os
import sys
import json
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add the parent directory to the path so we can import our project analysis modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import project analysis modules
from analyze_project_structure import analyze_project_structure
from detect_unused_media import detect_unused_media

app = Flask(__name__, static_folder='../build')
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size


@app.route('/api/analyze-project', methods=['POST'])
def analyze_project():
    """
    Analyze a CapCut project file and return the results.
    
    Expects a multipart/form-data request with a 'project_file' field containing
    the CapCut project file (usually draft_content.json).
    """
    if 'project_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['project_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.json'):
        return jsonify({'error': 'File must be a JSON file'}), 400
    
    # Save the uploaded file to a temporary location
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        # Analyze the project
        analysis_results = analyze_project_structure(file_path)
        
        # Detect unused media
        media_results = detect_unused_media(file_path)
        
        # Combine results
        results = {
            'structure': analysis_results,
            'media': media_results
        }
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the temporary file
        try:
            os.remove(file_path)
        except:
            pass


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve the React frontend."""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)