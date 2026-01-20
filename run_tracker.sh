#!/bin/bash
#
# Helper script to run the PCPC Agenda Tracker
#

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for API key
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY not set!"
    echo "Please create a .env file with your API key or export ANTHROPIC_API_KEY"
    exit 1
fi

# Run the tracker
echo ""
echo "Running PCPC Agenda Tracker..."
echo ""
python pcpc_agenda_tracker.py "$@"

# Deactivate virtual environment
deactivate
