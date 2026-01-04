#!/bin/bash
# SAM3 Drawing Segmenter - MVP Deployment Script

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SAM3 Drawing Segmenter - MVP Deployment${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Navigate to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi

if [ ! -f "models/sam3.pt" ]; then
    echo -e "${RED}❌ SAM3 model not found at models/sam3.pt${NC}"
    echo -e "${YELLOW}Run: python scripts/download_model.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}\n"

# Step 2: Check/create database
echo -e "${YELLOW}[2/6] Checking database...${NC}"

if [ ! -f "data/sam3.db" ]; then
    echo -e "${YELLOW}Creating database...${NC}"
    source .venv/bin/activate
    python scripts/create_database.py
    echo -e "${GREEN}✅ Database created${NC}\n"
else
    echo -e "${GREEN}✅ Database exists${NC}\n"
fi

# Step 3: Check for existing processes
echo -e "${YELLOW}[3/6] Checking for running servers...${NC}"

BACKEND_PID=$(lsof -ti:8001 2>/dev/null || echo "")
FRONTEND_PID=$(lsof -ti:3005 2>/dev/null || echo "")

if [ ! -z "$BACKEND_PID" ]; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8001 (PID: $BACKEND_PID)${NC}"
    read -p "Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill -9 $BACKEND_PID
        echo -e "${GREEN}✅ Killed existing backend${NC}"
    else
        echo -e "${YELLOW}Skipping backend startup${NC}"
        SKIP_BACKEND=1
    fi
fi

if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 3005 (PID: $FRONTEND_PID)${NC}"
    read -p "Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill -9 $FRONTEND_PID
        echo -e "${GREEN}✅ Killed existing frontend${NC}"
    else
        echo -e "${YELLOW}Skipping frontend startup${NC}"
        SKIP_FRONTEND=1
    fi
fi

echo ""

# Step 4: Start backend
if [ -z "$SKIP_BACKEND" ]; then
    echo -e "${YELLOW}[4/6] Starting backend server...${NC}"

    source .venv/bin/activate

    # Start backend in background with logging
    nohup uvicorn src.sam3_segmenter.main:app --reload --port 8001 --host 0.0.0.0 \
        > logs/backend.log 2>&1 &

    BACKEND_PID=$!
    echo $BACKEND_PID > logs/backend.pid

    echo -e "${BLUE}Backend PID: $BACKEND_PID${NC}"
    echo -e "${BLUE}Waiting for backend to start...${NC}"

    # Wait for backend to be ready (max 30 seconds)
    for i in {1..30}; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend started successfully${NC}"
            echo -e "${GREEN}   URL: http://localhost:8001${NC}"
            echo -e "${GREEN}   Logs: logs/backend.log${NC}\n"
            break
        fi
        sleep 1
        echo -n "."
    done

    if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "\n${RED}❌ Backend failed to start${NC}"
        echo -e "${YELLOW}Check logs: tail -f logs/backend.log${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}[4/6] Skipping backend startup${NC}\n"
fi

# Step 5: Start frontend
if [ -z "$SKIP_FRONTEND" ]; then
    echo -e "${YELLOW}[5/6] Starting frontend server...${NC}"

    cd sam3-ui

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
    fi

    # Start frontend in background with logging
    nohup npm run dev > ../logs/frontend.log 2>&1 &

    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid

    cd ..

    echo -e "${BLUE}Frontend PID: $FRONTEND_PID${NC}"
    echo -e "${BLUE}Waiting for frontend to start...${NC}"

    # Wait for frontend to be ready (max 20 seconds)
    for i in {1..20}; do
        if curl -s http://localhost:3005 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend started successfully${NC}"
            echo -e "${GREEN}   URL: http://localhost:3005${NC}"
            echo -e "${GREEN}   Logs: logs/frontend.log${NC}\n"
            break
        fi
        sleep 1
        echo -n "."
    done

    if ! curl -s http://localhost:3005 > /dev/null 2>&1; then
        echo -e "\n${RED}❌ Frontend failed to start${NC}"
        echo -e "${YELLOW}Check logs: tail -f logs/frontend.log${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}[5/6] Skipping frontend startup${NC}\n"
fi

# Step 6: Summary
echo -e "${YELLOW}[6/6] Deployment summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ SAM3 MVP is now running!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${BLUE}🌐 Access Points:${NC}"
echo -e "   Frontend UI:  ${GREEN}http://localhost:3005${NC}"
echo -e "   Backend API:  ${GREEN}http://localhost:8001${NC}"
echo -e "   API Docs:     ${GREEN}http://localhost:8001/docs${NC}\n"

echo -e "${BLUE}📊 System Status:${NC}"
curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "   Backend not responding"
echo ""

echo -e "${BLUE}📁 Log Files:${NC}"
echo -e "   Backend:  logs/backend.log"
echo -e "   Frontend: logs/frontend.log\n"

echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   View backend logs:  ${GREEN}tail -f logs/backend.log${NC}"
echo -e "   View frontend logs: ${GREEN}tail -f logs/frontend.log${NC}"
echo -e "   Stop servers:       ${GREEN}./scripts/stop_mvp.sh${NC}\n"

echo -e "${YELLOW}📖 Next Steps:${NC}"
echo -e "   1. Open http://localhost:3005 in your browser"
echo -e "   2. Upload an engineering drawing (PNG/JPEG)"
echo -e "   3. Click 'Segment Drawing' button"
echo -e "   4. Review the detected zones and page type\n"

echo -e "${GREEN}Happy Testing! 🚀${NC}"
