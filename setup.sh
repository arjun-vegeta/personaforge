#!/bin/bash

# PersonaForge Quick-Start Setup Script
# This script sets up the local Python virtual environment, installs dependencies,
# scaffolds the project folders, and configures the environment file.

set -e

echo "========================================="
echo "PersonaForge Local Setup Utility"
echo "========================================="

# 1. Check Prerequisites
echo "Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.10+ and retry."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Warning: Node.js is not installed. You will not be able to run the web dashboard locally."
fi

# 2. Virtual Environment Configuration
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created in venv/"
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate

# 3. Install Dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest-mock pytest-asyncio

# 4. Configure Environment Variables
echo "Configuring environment keys..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from .env.example. Please open .env and add your API keys."
    else
        touch .env
        echo "Created blank .env file. Please add GOOGLE_API_KEY and ELEVENLABS_API_KEY."
    fi
else
    echo ".env file already exists."
fi

# 5. Initialize PersonaForge Project
echo "Initializing project folders..."
export PYTHONPATH=$PYTHONPATH:.
python3 -m personaforge.backend.app.cli.main init

echo ""
echo "========================================="
echo "Setup Completed Successfully!"
echo "========================================="
echo "To start using PersonaForge:"
echo ""
echo "1. Activate the environment:"
echo "   source venv/bin/activate"
echo "   export PYTHONPATH=\$PYTHONPATH:."
echo ""
echo "2. Open your .env file and add your API keys:"
echo "   GOOGLE_API_KEY=your_key_here"
echo "   ELEVENLABS_API_KEY=your_key_here"
echo ""
echo "3. Run a dry-run scenario test to verify:"
echo "   python3 -m personaforge.backend.app.cli.main run scenarios/telecom_refund.yaml --count 1 --dry-run"
echo ""
echo "4. (Optional) Run the web dashboard studio:"
echo "   Backend: uvicorn personaforge.backend.app.main:app --reload"
echo "   Frontend: cd personaforge/web && npm install && npm run dev"
echo "========================================="
echo ""
