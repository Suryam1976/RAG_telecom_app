@echo off
echo 🚀 Setting up Telecom RAG Plan Advisor
echo ======================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo 📚 Installing requirements...
pip install -r requirements.txt

:: Install Playwright browsers
echo 🌐 Installing Playwright browsers...
playwright install chromium

:: Check for .env file
if not exist ".env" (
    echo ⚙️ Creating .env file from template...
    copy .env.example .env
    echo 📝 Please edit .env file and add your API keys:
    echo    - OPENAI_API_KEY=your_openai_key_here
    echo    - GROQ_API_KEY=your_groq_key_here
    echo.
)

:: Create necessary directories
echo 📁 Creating directories...
if not exist "chroma_db" mkdir chroma_db
if not exist "scraped_data" mkdir scraped_data

echo.
echo ✅ Setup complete!
echo.
echo 🔑 Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: streamlit run app.py
echo.
echo 🚀 To run the app now:
echo streamlit run app.py

pause
