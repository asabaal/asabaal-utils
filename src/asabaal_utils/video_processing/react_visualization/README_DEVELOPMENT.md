# CapCut Project Visualizer - Development Guide

This document provides instructions for setting up and running the CapCut Project Visualizer for development.

## Project Structure

The project consists of two main parts:

1. **React Frontend**: Interactive UI for visualizing CapCut projects
2. **Python Backend**: Flask API for analyzing project files

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- Python (v3.8 or higher)
- pip

## Setting Up the Frontend

1. Navigate to the project directory:
   ```
   cd /path/to/asabaal-utils/src/asabaal_utils/video_processing/react_visualization
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

   This will start the React development server at [http://localhost:3000](http://localhost:3000)

## Setting Up the Backend

1. Navigate to the backend directory:
   ```
   cd /path/to/asabaal-utils/src/asabaal_utils/video_processing/react_visualization/backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the Flask server:
   ```
   python server.py
   ```

   This will start the backend API server at [http://localhost:5000](http://localhost:5000)

## Development Workflow

1. Run both the frontend and backend servers as described above.
2. The frontend will proxy API requests to the backend.
3. Make changes to the React components in the `src` directory.
4. Make changes to the Python backend in the `backend` directory.

## Building for Production

1. Build the React app:
   ```
   npm run build
   ```

2. The built files will be in the `build` directory. The Flask server is configured to serve these static files.

3. To run the production build:
   ```
   cd backend
   python server.py
   ```

   Then access the application at [http://localhost:5000](http://localhost:5000)

## Deployment Options

1. **Flask-hosted**: The simplest approach is to build the React app and let Flask serve it as shown above.

2. **Separate hosting**:
   - Host the React build on a static site hosting service (Netlify, Vercel, etc.)
   - Deploy the Flask backend as a separate service
   - Configure CORS and API endpoints accordingly

3. **Electron packaging**:
   - For a desktop application, you can package with Electron
   - This requires additional setup not covered in this guide

## Troubleshooting

- If the backend fails to start, check if the required Python modules are installed and if port 5000 is available.
- If the frontend cannot connect to the backend, check that the backend is running and the proxy is configured correctly in `package.json`.
- For other issues, check the console output in the browser and the terminal running the backend for error messages.