# 🚀 Enterprise-Ready RAG Pipeline

A robust, modular, and production-oriented framework for building Retrieval-Augmented Generation (RAG) applications. This project features a FastAPI backend and a modern React frontend styled with Tailwind CSS, designed for enterprise use cases with a focus on configuration-driven design, cost-efficiency, and extensibility.

## 🌟 Features

### Backend
-   **Document Processing**: Supports multiple formats (PDF, DOCX, TXT), performs smart chunking, and uses checksum verification to avoid redundant processing.
-   **Vector Storage**: Utilizes ChromaDB for persistent vector storage, enabling efficient similarity searches and automatic embedding generation.
-   **LLM Integration**: Powered by Groq for fast inference, with support for configurable models and different LLM providers.
-   **API Layer**: A robust RESTful API built with FastAPI, featuring WebSocket support for real-time communication and comprehensive, auto-generated documentation.

### Frontend
-   **Modern React Interface**: A clean, responsive design built with React and styled with Tailwind CSS.
-   **Real-time Chat**: A fully interactive chat interface with real-time message streaming.
-   **Rich Functionality**: Features include document upload and management, conversation history, Markdown rendering, source attribution, and user feedback on messages.
-   **Customizable**: Supports light/dark themes and a settings panel for configuring the AI model.

## 🏗️ Project Structure

```
rag_llm/
├── chroma_store/          # Vector database storage
├── data/                  # Document storage (raw and processed)
├── frontend/              # React + Tailwind CSS frontend
├── src/                   # Python backend source code
│   ├── api.py             # FastAPI application
│   ├── config.py          # Configuration settings
│   ├── embed_store.py     # Vector store operations
│   ├── ingest.py          # Document processing
│   ├── llm.py             # LLM integration
│   └── main.py            # CLI entry point
├── tests/                 # Test files
├── .env                   # Environment variables
├── environment.yml        # Conda environment definition
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
-   Python 3.9+
-   Node.js 18+ and npm 9+
-   Conda (recommended for Python environment management)

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd rag_llm
    ```

2.  **Set Up the Backend**
    -   **Create Environment**:
        ```bash
        # Using conda (recommended)
        conda env create -f environment.yml
        conda activate rag_llm

        # Or with a standard virtual environment
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        pip install -r requirements.txt
        ```
    -   **Configure Environment Variables**: Create a `.env` file in the project root.
        ```env
        # Required for LLM integration
        GROQ_API_KEY=your_groq_api_key_here

        # Optional: For using OpenAI models
        OPENAI_API_KEY=your_openai_key_here
        ```

3.  **Set Up the Frontend**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

## 🖥️ Usage

1.  **Start the Backend Server**
    From the project root, run:
    ```bash
    uvicorn src.api:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

2.  **Start the Frontend Development Server**
    In a **new terminal**, from the project root, run:
    ```bash
    cd frontend
    npm start
    ```
    The web interface will be available at `http://localhost:3000`.

3.  **Upload Documents and Chat**
    -   Navigate to the "Browse Documents" page to upload your files.
    -   Return to the "New Chat" page to start asking questions!

### Using the Backend CLI (Optional)

You can also interact with the RAG pipeline directly via the command line.

-   **Index a document**:
    ```bash
    python -m src.main index --file path/to/your/document.pdf
    ```
-   **Query the system**:
    ```bash
    python -m src.main query "Your question here"
    ```

## 🧪 Testing

To run the backend test suite, use `pytest` from the project root:
```bash
pytest
```

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

This project is distributed under the MIT License. See the `LICENSE` file for more information.