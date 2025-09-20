#!/bin/bash

# Exit on error
set -e

echo "🚀 Setting up RAG LLM Application..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.8 or higher is required. Please install it first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Please install it first."
    exit 1
fi

# Create and activate virtual environment
echo "🔧 Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up frontend
echo "💻 Setting up frontend..."
cd frontend
npm install
cd ..

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    echo "# API Configuration" > .env
    echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
    echo "" >> .env
    echo "# Application Settings" >> .env
    echo "CHUNK_SIZE=1000" >> .env
    echo "CHUNK_OVERLAP=200" >> .env
    echo "VECTOR_STORE_PATH=./chroma_store" >> .env

    echo "✅ Created .env file. Please update it with your Groq API key."
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start the application, run:"
echo ""
echo "1. Start the backend server:"
echo "   source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate"
echo "   uvicorn src.api:app --reload"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "The application will be available at http://localhost:3000"
echo ""
echo "Happy coding! 🚀"
