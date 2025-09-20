# 🚀 Enterprise-Ready RAG Pipeline

A robust, modular, and production-oriented framework for building Retrieval-Augmented Generation (RAG) applications. Features a FastAPI backend and React frontend, designed for enterprise use cases with configuration-driven design, cost-efficiency, and extensibility.

## 🌟 Features

### Backend
- **Document Processing**
  - Supports multiple formats: PDF, DOCX, TXT
  - Smart chunking with configurable parameters
  - Checksum verification to avoid redundant processing
  
- **Vector Storage**
  - Persistent storage with ChromaDB
  - Efficient similarity search
  - Automatic embedding generation
  
- **LLM Integration**
  - Powered by Groq for fast inference
  - Configurable models and parameters
  - Support for different LLM providers
  
- **API Layer**
  - RESTful API with FastAPI
  - WebSocket support for real-time updates
  - Comprehensive API documentation

### Frontend
- **Modern React Interface**
  - Clean, responsive design
  - Real-time chat interface
  - Document upload and management
  - Conversation history

## 🏗️ Project Structure

```
rag_llm/
├── chroma_store/          # Vector database storage
├── data/                  # Document storage
│   ├── raw/               # Original documents
│   └── processed/         # Processed chunks and metadata
├── frontend/              # React frontend
│   ├── public/            # Static assets
│   └── src/               # React source code
├── src/                   # Python source code
│   ├── prompts/           # Prompt templates
│   ├── api.py             # FastAPI application
│   ├── config.py          # Configuration settings
│   ├── embed_store.py     # Vector store operations
│   ├── ingest.py          # Document processing
│   ├── llm.py             # LLM integration
│   └── main.py            # CLI entry point
├── tests/                 # Test files
├── .env                   # Environment variables
├── environment.yml        # Conda environment
├── requirements.txt       # Python dependencies
└── setup.sh               # Setup script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Conda (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rag_llm
   ```

2. **Set up Python environment**
   ```bash
   # Using conda (recommended)
   conda env create -f environment.yml
   conda activate rag_llm
   
   # Or with virtualenv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   # API Keys
   OPENAI_API_KEY=your_openai_key
   GROQ_API_KEY=your_groq_key
   
   # Application Settings
   DEBUG=True
   CHROMA_DB_PATH=./chroma_store
   ```

## 🖥️ Usage

### Backend (CLI)

1. **Index documents**
   ```bash
   python -m src.main index --file data/raw/your_document.pdf
   ```

2. **Query the system**
   ```bash
   python -m src.main query "Your question here"
   ```

### Web Interface

1. **Start the backend server**
   ```bash
   uvicorn src.api:app --reload
   ```

2. **Start the frontend**
   ```bash
   cd frontend
   npm start
   ```

3. Open `http://localhost:3000` in your browser

## 📚 API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

Run the test suite with:
```bash
pytest tests/
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

## 📚 Resources

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://www.trychroma.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)

```
rag_llm/
├── data/                    # Raw and processed documents
│   ├── raw/                 # Original documents
│   └── processed/           # Processed chunks and checksums
├── frontend/                # React frontend
├── src/                     # Backend source code
│   ├── api.py               # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── embed_store.py       # Vector store operations
│   ├── ingest.py            # Document processing
│   ├── llm.py               # LLM initialization
│   └── prompts/             # Prompt templates
└── tests/                   # Test files
```

## Setup

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the project root with:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Start the Backend

```bash
uvicorn src.api:app --reload
```

The API will be available at `http://localhost:8000`

### Start the Frontend

In a new terminal:

```bash
cd frontend
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

- `GET /health` - Health check
- `POST /ingest` - Upload and index a document
- `POST /query` - Query the RAG system

## Development

### Testing

Run tests with:

```bash
pytest
```

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key
- `CHUNK_SIZE`: Document chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `VECTOR_STORE_PATH`: Path to store vector database (default: "./chroma_store")

## License

MIT
