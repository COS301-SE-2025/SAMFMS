#!/bin/bash
# SAMFMS Mock Data Generation Script
# Quick setup and execution for Unix/Linux/macOS systems

set -e  # Exit on any error

echo "🚀 SAMFMS Mock Data Generator"
echo "=============================="
echo ""
echo "🔐 Note: You will be prompted for your SAMFMS password"
echo "   Email: mvanheerdentuks@gmail.com"
echo "   (Password input will be hidden for security)"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "config.py" ]; then
    echo "❌ Please run this script from the mock_scripts directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
python3 -m pip install -q aiohttp

# Check if services are running
echo "🔍 Checking SAMFMS services..."
if ! curl -s http://localhost:21000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Core service (port 21000) may not be running"
fi

if ! curl -s http://localhost:21004/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Maintenance service (port 21004) may not be running"
fi

# Parse command line arguments
QUICK_MODE=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --quick    Run quick test with minimal data"
            echo "  --verbose  Enable verbose logging"
            echo "  --help     Show this help message"
            exit 0
            ;;
    esac
done

# Run the mock data generation
echo "🎬 Starting mock data generation..."

if [ "$QUICK_MODE" = true ]; then
    echo "🧪 Running in quick test mode..."
    if [ "$VERBOSE" = true ]; then
        python3 create_all_mock_data.py --quick --verbose
    else
        python3 create_all_mock_data.py --quick
    fi
else
    echo "🏭 Running full data generation..."
    if [ "$VERBOSE" = true ]; then
        python3 create_all_mock_data.py --verbose
    else
        python3 create_all_mock_data.py
    fi
fi

echo "✅ Mock data generation completed!"
echo ""
echo "💡 Next steps:"
echo "   1. Check the SAMFMS web interface"
echo "   2. Verify data via API endpoints"
echo "   3. Review service logs for any issues"
