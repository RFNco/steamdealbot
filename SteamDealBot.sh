#!/bin/bash

# SteamDealBot - Manual Poster for macOS
# A shell script to launch the SteamDealBot manual poster

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Clear screen and show header
clear
echo -e "${BLUE}========================================"
echo -e "   🎮 SteamDealBot - Manual Poster 🎮"
echo -e "========================================${NC}"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed or not in PATH${NC}"
    echo "Please install Python 3 from https://python.org or using Homebrew:"
    echo "  brew install python3"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "manual_poster.py" ]; then
    echo -e "${RED}❌ Cannot find manual_poster.py${NC}"
    echo "Please make sure you're in the SteamDealBot folder"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found${NC}"
echo -e "${GREEN}✅ Project files found${NC}"
echo

# Check if required packages are installed
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"

# Install essential packages individually to avoid build issues
echo -e "${YELLOW}📦 Installing essential packages...${NC}"

# Install requests (essential for API calls)
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing requests...${NC}"
    pip3 install requests
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ requests installed${NC}"
    else
        echo -e "${RED}❌ Failed to install requests${NC}"
    fi
else
    echo -e "${GREEN}✅ requests already installed${NC}"
fi

# Install beautifulsoup4 (for HTML parsing)
python3 -c "import bs4" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing beautifulsoup4...${NC}"
    pip3 install beautifulsoup4
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ beautifulsoup4 installed${NC}"
    else
        echo -e "${RED}❌ Failed to install beautifulsoup4${NC}"
    fi
else
    echo -e "${GREEN}✅ beautifulsoup4 already installed${NC}"
fi

# Install pyperclip (for clipboard functionality)
python3 -c "import pyperclip" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing pyperclip...${NC}"
    pip3 install pyperclip
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ pyperclip installed${NC}"
    else
        echo -e "${RED}❌ Failed to install pyperclip${NC}"
    fi
else
    echo -e "${GREEN}✅ pyperclip already installed${NC}"
fi

# Try to install lxml (optional, for better HTML parsing)
echo -e "${YELLOW}Trying to install lxml (optional)...${NC}"
python3 -c "import lxml" 2>/dev/null
if [ $? -ne 0 ]; then
    pip3 install lxml 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ lxml installed${NC}"
    else
        echo -e "${YELLOW}⚠️  lxml installation failed (not critical)${NC}"
    fi
else
    echo -e "${GREEN}✅ lxml already installed${NC}"
fi

echo -e "${GREEN}✅ Essential dependencies check completed${NC}"

echo
echo -e "${BLUE}Starting SteamDealBot...${NC}"
echo

# Run the bot
python3 manual_poster.py

echo
echo -e "${BLUE}========================================"
echo -e "Bot execution completed!"
echo -e "========================================${NC}"
echo
read -p "Press Enter to exit..."
