#!/bin/bash
# Script to start both frontend and backend development servers

# Start the backend in the background
echo "Starting Flask backend server..."
cd backend
python server.py &
BACKEND_PID=$!
cd ..

# Wait a moment for the backend to start
sleep 2

# Start the frontend
echo "Starting React frontend server..."
npm start

# When the frontend is stopped, also stop the backend
echo "Stopping Flask backend server..."
kill $BACKEND_PID