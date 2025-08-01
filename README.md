# ADAS Diagnostics Co-pilot

An AI-powered automotive diagnostics assistant built with FastAPI, Streamlit, and advanced RAG (Retrieval-Augmented Generation) capabilities. This system helps automotive technicians and engineers diagnose vehicle issues using natural language queries against a comprehensive knowledge base of automotive documentation.

## 🚗 Features

- **Intelligent Document Processing**: Automatically processes automotive documents (OTA updates, hardware specs, diagnostic logs)
- **Vector Search**: Semantic search across automotive documentation using embeddings
- **Knowledge Graph**: Neo4j-powered relationship mapping between automotive components and systems
- **Multi-Modal AI**: Supports both Gemini and OpenAI models for different use cases
- **Real-time Chat Interface**: Streamlit-based web interface for interactive diagnostics
- **Session Management**: Persistent conversation history and context
- **Automotive Entity Extraction**: Automatically identifies components, systems, DTCs, and relationships

## 🏗️ Architecture

- **Backend**: FastAPI with async PostgreSQL and Neo4j
- **Frontend**: Streamlit web application
- **Database**: PostgreSQL with pgvector extension for embeddings
- **Knowledge Graph**: Neo4j for entity relationships
- **AI Models**: Gemini 2.0 Flash (default) with fallback to OpenAI
- **Containerization**: Podman for database services

## 📋 Prerequisites

- Python 3.11+
- Podman (for container management)
- Task (task runner) - Install from [taskfile.dev](https://taskfile.dev/installation/)
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rag-adas-diagnose
```

### 2. Set Up Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Gemini API Key (get from https://aistudio.google.com/app/apikey)
GOOGLE_API_KEY=your-gemini-api-key-here
llm_api_key=your-gemini-api-key-here

# For embeddings, we use Gemini by default
embedding_api_key=your-gemini-api-key-here
embedding_provider=gemini
```

### 3. Create Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Install dependencies
python3.11 -m pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Google API key
# Get your API key from https://aistudio.google.com/app/apikey
```

Example `.env` configuration:

```env
# LLM Configuration (Using Gemini AI as default)
GOOGLE_API_KEY=your-google-api-key-here
llm_api_key=your-google-api-key-here
llm_provider=gemini
llm_choice=gemini-2.0-flash

# Optional: Database Configuration (for full functionality)
DATABASE_URL=postgresql://adas_user:adas_password@localhost:5435/adas_diagnostics
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Embedding Configuration (keeping OpenAI for embeddings)
embedding_api_key=your-openai-api-key
embedding_provider=openai
embedding_model=text-embedding-3-small
OPENAI_API_KEY=your-openai-api-key
```

### 3. Start the application (Basic Mode)

For basic functionality without databases:

```bash
# Start the FastAPI backend
python -m agent.api &

# Start the Streamlit frontend
streamlit run app.py
```

The application will be available at http://localhost:8501 (Streamlit) with the API at http://localhost:8058.

### 3. Advanced Setup (With Databases)

For full functionality with document ingestion and knowledge graphs:

```bash
# Install Task runner (if not already installed)
# On macOS: brew install go-task/tap/go-task
# On Linux: sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin

# Set up the complete environment (containers + database initialization)
task setup

# Or run individual steps:
# task containers:start  # Start containers
# task db:wait          # Wait for databases to be ready
# task db:init          # Initialize database schema
```

**For existing databases:** If you have an existing database without session management tables, run the migration:

```bash
# Check if your database has all required tables
python scripts/check_database.py

# If session tables are missing, run the migration
python scripts/migrate_database.py
```

### 4. Document Ingestion (Advanced Mode Only)

```bash
# Add your documents to the data/sample-data folder or create automotive_docs folder
mkdir -p automotive_docs
# Copy your OTA release notes, hardware specs, diagnostic logs, etc.

# Process and ingest automotive documents
python -m ingestion.ingest

# Or ingest real documents
python scripts/ingest_real_documents.py

# This will:
# - Parse and semantically chunk your documents
# - Generate embeddings for vector search
# - Extract entities and relationships for the knowledge graph
# - Store everything in PostgreSQL and Neo4j
```

## Project Structure

```
rag-adas-diagnose/
├── agent/                  # AI agent and API
│   ├── agent.py           # Main Pydantic AI agent
│   ├── api.py             # FastAPI application
│   ├── config.py          # Configuration management
│   ├── db_utils.py        # Database utilities
│   ├── graph_utils.py     # Knowledge graph utilities
│   ├── models.py          # Data models
│   └── tools.py           # Agent tools
├── ingestion/             # Document processing
│   ├── document_processor.py  # Document processing
│   ├── embedding_service.py   # Embedding generation
│   ├── entity_extractor.py    # Entity extraction
│   └── ingest.py             # Main ingestion pipeline
├── scripts/               # Utility scripts
│   ├── check_database.py     # Database health check
│   ├── migrate_database.py   # Database migrations
│   └── ingest_real_documents.py  # Document ingestion
├── data/                  # Sample data and documents
│   └── sample-data/       # Sample automotive documents
├── docs/                  # Documentation
│   └── prd.md            # Product requirements
├── sql/                   # Database schema
│   ├── init.sql          # Initial schema
│   └── migrate_add_sessions.sql  # Session tables
├── tests/                 # Test suite
├── ui/                    # UI components
├── app.py                 # Streamlit frontend
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
└── README.md             # This file
```

## Core Features

### Timeline Analysis
Query for chronological events related to specific vehicle systems or VINs:
```
"Show the timeline of all software updates and component changes for the ADAS system in the last 60 days for VIN WXYZ123."
```

### Dependency and Relationship Mapping
Understand component interactions and failure domains:
```
"What are the documented dependencies of the 'Lane Keep Assist' module?"
```

### Hybrid Search for Root Cause Analysis
Describe failure symptoms in natural language:
```
"The vehicle's emergency braking system is activating randomly in clear weather. What are the possible causes based on recent software updates and sensor specifications?"
```

## Supported Document Types

- **OTA Update Release Notes** (.md, .txt, .pdf)
- **Hardware Datasheets** (.pdf, .md)
- **System Architecture Documents** (.md, .pdf)
- **Diagnostic Trouble Code databases** (.csv, .json)
- **Technician Repair Notes** (.md, .txt)
- **Supplier Documentation** (.pdf, .md)

## Configuration

Key environment variables:
- `LLM_PROVIDER`: Choose from openai, ollama, openrouter, gemini
- `DATABASE_URL`: PostgreSQL connection string
- `NEO4J_URI`: Neo4j connection URI
- `APP_PORT`: Application port (default: 8058)

See `.env.example` for complete configuration options.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agent --cov=ingestion --cov-report=html

# Run specific test categories
pytest tests/agent/
pytest tests/ingestion/
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy agent/ ingestion/
```

## Quick Demo

Want to try the system immediately? Follow these steps:

1. **Get a Google API Key**: Visit https://aistudio.google.com/app/apikey
2. **Set up the environment**:
   ```bash
   git clone <repository-url>
   cd rag-adas-diagnose
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure Gemini AI**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   ```
4. **Start the application**:
   ```bash
   python -m agent.api &
   streamlit run app.py
   ```
5. **Try sample questions** from [docs/demo.md](docs/demo.md)

## Documentation

- [Demo Questions and Examples](docs/demo.md) - Sample questions to try with the system
- [Product Requirements](docs/prd.md) - Detailed product specifications
- [API Documentation](http://localhost:8058/docs) - FastAPI auto-generated docs (when running)

## Troubleshooting

**Common Issues:**

1. **"Unknown model" error**: Make sure you have the latest pydantic-ai version (0.4.7+)
2. **API key issues**: Verify your Google API key is correctly set in the .env file
3. **Database connection errors**: These are expected in basic mode - the system will work without databases
4. **Import errors**: Ensure you're using Python 3.11+ and have activated the virtual environment

### Database Connection Issues (Advanced Mode)
Ensure Podman containers are running:
```bash
task status
task logs
task health
```

### No Results from Agent (Advanced Mode)
Make sure you've run the ingestion pipeline:
```bash
python -m ingestion.ingest --verbose
```

### LLM API Issues
Check your API key and provider configuration in `.env`

## ✅ Verified Working Setup (Updated)

**All issues have been resolved!** The system now works end-to-end with the following setup:

### Quick Start (Recommended)

1. **Prerequisites**: Install Task runner from [taskfile.dev](https://taskfile.dev/installation/)

2. **Setup**:
   ```bash
   git clone <repository-url>
   cd rag-adas-diagnose
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure API Key**:
   ```bash
   # Edit .env and add your Gemini API key
   GOOGLE_API_KEY=your-gemini-api-key-here
   ```

4. **Start Everything**:
   ```bash
   task setup          # Start databases
   task ingest:sample  # Process sample data
   task app:start      # Start application
   ```

5. **Access**: http://localhost:8501

### Available Task Commands

```bash
# Container Management
task setup          # Complete environment setup
task cleanup         # Remove all containers and data
task status          # Show container status
task health          # Check service health

# Application
task app:start       # Start both API and frontend
task app:api         # Start FastAPI backend only
task app:frontend    # Start Streamlit frontend only
task app:test        # Run tests

# Data Ingestion
task ingest:sample                    # Process sample data
task ingest:file -- path/to/file.md  # Process single file
task ingest:directory -- path/to/dir # Process directory

# Database
task postgres:shell  # Connect to PostgreSQL
task neo4j:shell     # Connect to Neo4j
```

### What's Fixed

- ✅ Database initialization and connection issues
- ✅ Gemini embedding service integration (768 dimensions)
- ✅ Entity extraction type mismatches
- ✅ Document processing pipeline
- ✅ Vector database schema migration
- ✅ All Taskfile commands working
- ✅ Sample data ingestion working
- ✅ API and frontend startup

### Verified Features

- 📄 Document ingestion (3 sample documents processed)
- 🔍 Vector search with Gemini embeddings
- 🧠 Entity extraction (62 entities extracted)
- 💾 PostgreSQL + Neo4j integration
- 🌐 Streamlit web interface
- 🔌 FastAPI backend with docs
- 📊 Session management

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

---

Built with ❤️ for automotive diagnostics teams worldwide.
