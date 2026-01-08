#!/bin/bash
# Installation script for backend dependencies

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3.12 -m venv .venv
else
  echo "Upgrading virtual environment..."
  python3.12 -m venv --upgrade .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Installation complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
