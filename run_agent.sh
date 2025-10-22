#!/bin/bash

# MCP Agent Runner Script
# This script runs the MCP agent client with a given prompt
# Usage: ./run_agent.sh "your prompt here" [--verbose]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR" || exit 1

# Check if a prompt was provided
if [ $# -eq 0 ]; then
    echo "Error: No prompt provided"
    echo "Usage: ./run_agent.sh \"your prompt here\" [--verbose]"
    echo ""
    echo "Examples:"
    echo "  ./run_agent.sh \"Check the humidity and send a notification\""
    echo "  ./run_agent.sh \"What's the current temperature?\" --verbose"
    exit 1
fi

# Check if Python virtual environment exists
if [ -d ".venv" ]; then
    # Activate virtual environment
    source .venv/bin/activate
elif [ -f "pyproject.toml" ]; then
    echo "Warning: Virtual environment not found. Attempting to use system Python..."
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    exit 1
fi

# Run the client and let it complete fully - no time limits
python agents/client.py "$@"
