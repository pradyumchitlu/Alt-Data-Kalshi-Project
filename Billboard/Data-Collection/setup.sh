#!/bin/bash
# Setup script for Billboard Hot 100 Data Collection System

echo "=========================================="
echo "Billboard Hot 100 Data Collection Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Creating necessary directories..."
mkdir -p data
mkdir -p logs

echo ""
echo "=========================================="
echo "Setup Instructions:"
echo "=========================================="
echo ""
echo "1. Create a .env file with your configuration:"
echo "   cp .env.example .env  (if you have .env.example)"
echo "   OR create .env manually with:"
echo ""
echo "   DB_HOST=localhost"
echo "   DB_PORT=5432"
echo "   DB_NAME=billboard_data"
echo "   DB_USER=postgres"
echo "   DB_PASSWORD=your_password"
echo ""
echo "2. Set up PostgreSQL database:"
echo "   createdb billboard_data"
echo ""
echo "3. Initialize database tables:"
echo "   python3 database.py"
echo ""
echo "4. Run initial data collection:"
echo "   python3 main_collector.py"
echo ""
echo "5. (Optional) Start automated scheduler:"
echo "   python3 scheduler.py"
echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="

