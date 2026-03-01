#!/bin/bash

# HALO Health Startup Script
# This script starts both the FastAPI backend and the React frontend concurrently.

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting HALO Health Platform...${NC}"

# Function to handle cleanup on exit (Ctrl+C)
cleanup() {
    echo -e "\n${RED}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servers successfully stopped. Goodbye!${NC}"
    exit 0
}

# Catch termination signals
trap cleanup SIGINT SIGTERM EXIT

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Step 1: Backend Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
cd backend
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}-> Creating virtual environment...${NC}"
    python3 -m venv .venv
fi
echo -e "${GREEN}-> Installing backend dependencies...${NC}"
source .venv/bin/activate
pip install -r requirements.txt
cd ..

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}Step 2: Frontend Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
cd frontend-react
if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}-> Installing frontend dependencies...${NC}"
    npm install
fi
cd ..

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}Step 3: Starting Servers${NC}"
echo -e "${BLUE}=========================================${NC}"
# Start the Backend
echo -e "${GREEN}-> Starting FastAPI Backend on port 8000...${NC}"
backend/.venv/bin/python -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Give the backend a moment to spin up
sleep 2

# Start the Frontend
echo -e "${GREEN}-> Starting React Frontend on port 5173...${NC}"
cd frontend-react
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}🚀 HALO Health is now running!${NC}"
echo -e "Frontend UI: ${BLUE}http://localhost:5173${NC}"
echo -e "Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "Read the logs above. Press ${RED}Ctrl+C${NC} to stop all servers."

# Keep script running and wait for user to interrupt
wait
