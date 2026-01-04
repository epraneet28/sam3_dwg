#!/bin/bash
# SAM3 Drawing Segmenter - Stop MVP Script

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Stopping SAM3 MVP servers...${NC}\n"

cd "$(dirname "$0")/.."

# Stop backend
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill -9 $BACKEND_PID
        echo -e "${GREEN}✅ Stopped backend (PID: $BACKEND_PID)${NC}"
        rm logs/backend.pid
    else
        echo -e "${YELLOW}⚠️  Backend process not found${NC}"
        rm logs/backend.pid
    fi
else
    # Try finding by port
    BACKEND_PID=$(lsof -ti:8001 2>/dev/null)
    if [ ! -z "$BACKEND_PID" ]; then
        kill -9 $BACKEND_PID
        echo -e "${GREEN}✅ Stopped backend (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  No backend running on port 8001${NC}"
    fi
fi

# Stop frontend
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill -9 $FRONTEND_PID
        echo -e "${GREEN}✅ Stopped frontend (PID: $FRONTEND_PID)${NC}"
        rm logs/frontend.pid
    else
        echo -e "${YELLOW}⚠️  Frontend process not found${NC}"
        rm logs/frontend.pid
    fi
else
    # Try finding by port
    FRONTEND_PID=$(lsof -ti:3005 2>/dev/null)
    if [ ! -z "$FRONTEND_PID" ]; then
        kill -9 $FRONTEND_PID
        echo -e "${GREEN}✅ Stopped frontend (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  No frontend running on port 3005${NC}"
    fi
fi

echo -e "\n${GREEN}All servers stopped${NC}"
