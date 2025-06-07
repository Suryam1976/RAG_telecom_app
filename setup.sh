#!/bin/bash

# Telecom RAG App Setup and Run Script

echo "🚀 Setting up Telecom RAG Plan Advisor"
echo "======================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
if ! command_exists python; then
    echo "❌ Python is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install requirements
echo "📚 Installing requirements..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY=your_openai_key_here"
    echo "   - GROQ_API_KEY=your_groq_key_here"
    echo ""
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p chroma_db
mkdir -p scraped_data

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔑 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: streamlit run app.py"
echo ""
echo "🚀 To run the app now:"
echo "streamlit run app.py"
