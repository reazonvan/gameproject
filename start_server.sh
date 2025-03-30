#!/bin/bash
echo "Starting Game Trading Platform server..."
echo "======================================"

# Activate virtual environment if it exists
if [ -f .venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found, trying to run with system Python..."
fi

# Check if requirements are installed
echo "Checking dependencies..."
pip install -r requirements.txt

# Initialize database if needed
echo "Setting up database and static files..."
python main.py --init

# Start the server
echo "Starting server..."
python main.py

echo "Server is stopped" 