#!/bin/bash

# Quick Start Script for Smart Energy Monitoring System
# This script helps you get the system running quickly

set -e

echo "============================================="
echo "   Smart Energy Monitoring System"
echo "         Quick Start Guide"
echo "============================================="
echo ""

# Check if running from project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "This script will guide you through setting up the system."
echo ""

# Step 1: Check PostgreSQL
echo "Step 1: Checking PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running"
    echo "   Starting PostgreSQL..."
    sudo systemctl start postgresql
    sleep 2
    if systemctl is-active --quiet postgresql; then
        echo "✅ PostgreSQL started successfully"
    else
        echo "❌ Failed to start PostgreSQL. Please start it manually:"
        echo "   sudo systemctl start postgresql"
        exit 1
    fi
fi
echo ""

# Step 2: Database Setup
echo "Step 2: Database Setup"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw energy_monitoring; then
    echo "✅ Database 'energy_monitoring' already exists"
else
    echo "⚠️  Database not found. Running setup..."
    cd backend
    sudo bash setup_db.sh
    cd ..
    echo "✅ Database created and initialized"
fi
echo ""

# Step 3: Backend Setup
echo "Step 3: Backend Environment"
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    cd ..
    echo "✅ Backend environment ready"
else
    echo "✅ Backend virtual environment exists"
fi
echo ""

# Step 4: Frontend Setup
echo "Step 4: Frontend Dependencies"
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi
echo ""

# Step 5: Configuration Check
echo "Step 5: Configuration"
if [ ! -f "backend/.env" ]; then
    echo "Creating backend .env file from template..."
    cp backend/.env.example backend/.env
    echo "✅ Backend .env created (using defaults)"
else
    echo "✅ Backend .env exists"
fi

if [ ! -f "frontend/.env" ]; then
    echo "Creating frontend .env file..."
    echo "VITE_API_URL=http://localhost:8000" > frontend/.env
    echo "✅ Frontend .env created"
else
    echo "✅ Frontend .env exists"
fi
echo ""

# Step 6: Ready to Start
echo "============================================="
echo "✅ Setup Complete!"
echo "============================================="
echo ""
echo "To start the system, open TWO terminal windows:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  bash start.sh"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open your browser to:"
echo "  http://localhost:5173"
echo ""
echo "API Documentation will be available at:"
echo "  http://localhost:8000/docs"
echo ""
echo "============================================="
echo ""

read -p "Would you like to start the backend now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting backend..."
    echo "Note: Frontend will need to be started in a separate terminal"
    echo ""
    cd backend
    bash start.sh
fi
