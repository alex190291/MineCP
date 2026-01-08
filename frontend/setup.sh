#!/bin/bash

# Frontend Setup Script
# This script installs all dependencies and verifies the installation

echo "==================================="
echo "Minecraft Server Manager - Frontend Setup"
echo "==================================="
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js first."
    exit 1
fi

echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")"

echo "Installing dependencies..."
echo "This may take a few minutes..."
echo ""

# Install dependencies
npm install

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "Installation completed successfully!"
    echo "==================================="
    echo ""
    echo "Next steps:"
    echo "1. Start the dev server: npm run dev"
    echo "2. Open http://localhost:5173 in your browser"
    echo "3. Verify glassmorphism components are rendering"
    echo ""
    echo "Available commands:"
    echo "  npm run dev     - Start development server"
    echo "  npm run build   - Build for production"
    echo "  npm run preview - Preview production build"
    echo "  npm run lint    - Run ESLint"
    echo ""
else
    echo ""
    echo "==================================="
    echo "Installation failed!"
    echo "==================================="
    echo ""
    echo "Please check the error messages above and try again."
    exit 1
fi
