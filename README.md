# Agentic RAG System for Atlas University

A modular Retrieval-Augmented Generation (RAG) system developed for Atlas University in Istanbul, Turkey. This system supports multiple chatbots with different document repositories, databases, and prompt templates to assist students, administrators, and researchers.


## Features

- **Multiple Chatbots**: Support for different chatbots (StudentBot, AdminBot, AcademicBot) using the same core architecture
- **Modular Tools**: Document search, LLM-powered MongoDB queries, SQL queries, and web search via TavilySearch API
- **Self-RAG Implementation**: LLM-based tool selection that intelligently chooses which tools to use based on the query
- **Natural Language to MongoDB Query**: Automatic conversion of natural language questions to MongoDB queries using LLM
- **LangGraph Integration**: Agent development using the LangGraph framework
- **Conversation Memory**: Short-term memory for maintaining context across multiple interactions in a session
- **FastAPI Endpoints**: RESTful API for interacting with the chatbots
- **Configurable**: Easy configuration via YAML files without changing code

## Project Structure

```
Agentic RAG/
├── app/
│   ├── core/                    # Core system components
│   ├── tools/                   # Tool implementations
│   ├── models/                  # Data models
│   ├── agents/                  # Agent implementations
│   ├── document_processing/     # Document processing system
│   └── main.py                  # FastAPI application
├── configs/                     # Bot configuration files
├── prompts/                     # Prompt templates
├── data/                        # Document storage and processing
│   ├── raw/                     # Upload documents here
│   ├── processed/               # Processing metadata
│   └── chroma_stores/           # Vector store collections
├── scripts/                     # Utility scripts
├── examples/                    # Usage examples
├── docs/                        # Documentation
└── requirements.txt             # Project dependencies
```

## Installation

### Prerequisites

Before starting, you'll need:
- **OpenAI API Key**: Get one from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Tavily API Key**: Get one from [Tavily](https://tavily.com/)
- Docker and Docker Compose (for Docker installation)
- Python 3.11+ (for manual installation)

### Option 1: Docker Installation (Recommended)

Docker provides the easiest way to run the Agentic RAG system with all dependencies and services.

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (version 20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or higher)

#### Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/berkincetin/agentic-rag.git
   cd agentic-rag
   ```

2. Set up environment variables:
   Copy the example environment file and update with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env file with your actual API keys
   ```

3. Start the application:
   ```bash
   # Backend-only deployment (FastAPI + MongoDB)
   docker-compose -f docker-compose.backend-only.yml up --build -d
   ```

4. Access the services:
   - **API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

#### Docker Commands

```bash
# Start backend services
docker-compose -f docker-compose.backend-only.yml up --build -d

# View logs
docker-compose -f docker-compose.backend-only.yml logs -f agentic-rag

# Stop all services
docker-compose -f docker-compose.backend-only.yml down

# Rebuild and restart
docker-compose -f docker-compose.backend-only.yml up --build -d

# Clean up (remove volumes)
docker-compose -f docker-compose.backend-only.yml down -v
```

The Docker deployment includes:
- FastAPI backend service (port 8000)
- MongoDB database (port 27017)
- Automatic database initialization
- Health checks for both services
- Minimal dependencies for faster builds

#### Testing the Backend

Once the backend is running, you can test it:

```bash
# Check API health (PowerShell)
Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET

# View API documentation
# Open http://localhost:8000/docs in your browser

# Test a chatbot query (PowerShell)
$body = @{
    query = "Merhaba, nasılsın?"
    session_id = "test-session-1"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/bots/StudentBot/query" -Method POST -Body $body -ContentType "application/json; charset=utf-8"
```

### Option 2: Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/agentic-rag.git
   cd agentic-rag
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Copy the example environment file and update with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env file with your actual API keys
   ```

5. Install and start MongoDB:
   ```bash
   # Using Docker for MongoDB only
   docker run -d --name mongodb -p 27017:27017 mongo:7.0
   ```

## Docker Architecture

The Docker setup includes the following services:

### Backend Services (`docker-compose.backend-only.yml`)
- **agentic-rag**: Main FastAPI application
- **mongodb**: MongoDB database with initialization

### Docker Features
- **Multi-stage builds**: Optimized production images
- **Health checks**: Automatic service monitoring
- **Volume mounts**: Persistent data storage
- **Network isolation**: Secure inter-service communication
- **Turkish character support**: Proper UTF-8 encoding
- **Security**: Non-root user execution

### Environment Configuration

The Docker setup supports the following environment variables:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration (automatically set in Docker)
MONGODB_URL=mongodb://mongodb:27017/
```

### Data Persistence

Docker volumes are used for data persistence:
- `mongodb_backend_data`: MongoDB database files
- `./data`: Document storage and processing
- `./configs`: Bot configurations (read-only)
- `./prompts`: Prompt templates (read-only)

### Troubleshooting Docker

```bash
# Check service status
docker-compose -f docker-compose.backend-only.yml ps

# View service logs
docker-compose -f docker-compose.backend-only.yml logs agentic-rag
docker-compose -f docker-compose.backend-only.yml logs mongodb

# Restart a specific service
docker-compose -f docker-compose.backend-only.yml restart agentic-rag

# Access container shell
docker-compose -f docker-compose.backend-only.yml exec agentic-rag bash

# Check MongoDB connection
docker-compose -f docker-compose.backend-only.yml exec mongodb mongosh

# Monitor resource usage
docker stats
```

## Running the Application

### Starting the API Server

Start the FastAPI application with Uvicorn:

```
python -m app.main
```

Or directly with Uvicorn:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Running the Gradio UI (Optional)

Once the API server is running, you can start the optional Gradio UI:

```bash
python app/ui.py
```

The UI will be available at `http://localhost:7860`.

The Gradio UI provides:
- A dropdown to select which chatbot to talk to
- Information about the selected chatbot
- A chat interface to send messages and see responses
- **Full Turkish character support** with bilingual interface
- Automatic UTF-8 encoding for Windows compatibility
- Turkish/English labels and error messages


## API Endpoints

- `GET /`: Health check
- `GET /bots`: List all available bots
- `GET /bots/{bot_name}`: Get information about a specific bot
- `POST /bots/{bot_name}/query`: Query a specific bot
- `POST /bots/{bot_name}/clear-memory`: Clear conversation memory for a specific session
- `POST /reload`: Reload all bot configurations

## Using the API from the Terminal

### Windows PowerShell

#### Setting Up PowerShell for UTF-8 Support
To ensure proper handling of Turkish characters in PowerShell, run these commands at the beginning of your session:

```powershell
# Set PowerShell to use UTF-8 encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

> **IMPORTANT**: When making API requests with Turkish characters, always include `charset=utf-8` in the Content-Type header (`application/json; charset=utf-8`). This ensures proper encoding of Turkish characters in both the request and response.

#### Health Check
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8000/" | Select-Object -ExpandProperty Content
```

#### List All Bots
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8000/bots" | Select-Object -ExpandProperty Content
```

#### Get Bot Information
```powershell
Invoke-WebRequest -Method GET -Uri "http://localhost:8000/bots/StudentBot" | Select-Object -ExpandProperty Content
```

#### Query a Bot (English)
```powershell
$body = @{
    query = "What courses are available for computer science students?"
    session_id = "test-session-1"
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Method POST -Uri "http://localhost:8000/bots/StudentBot/query" -Body $body -ContentType "application/json; charset=utf-8" | Select-Object -ExpandProperty Content
```

#### Query a Bot (Turkish)
```powershell
# Ensure UTF-8 encoding for Turkish characters
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$body = @{
    query = "Merhaba, nasılsın?"
    session_id = "test-session-turkish"
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://localhost:8000/bots/StudentBot/query" -Body $body -ContentType "application/json; charset=utf-8" | Select-Object -ExpandProperty Content
```

#### Reload Bot Configurations
```powershell
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/reload" | Select-Object -ExpandProperty Content
```

### Linux/macOS (curl)

> **IMPORTANT**: When making API requests with Turkish characters, always include `charset=utf-8` in the Content-Type header (`application/json; charset=utf-8`). This ensures proper encoding of Turkish characters in both the request and response.

#### Health Check
```bash
curl -X GET http://localhost:8000/
```

#### List All Bots
```bash
curl -X GET http://localhost:8000/bots
```

#### Get Bot Information
```bash
curl -X GET http://localhost:8000/bots/StudentBot
```

#### Query a Bot
```bash
curl -X POST http://localhost:8000/bots/StudentBot/query \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"query": "What courses are available for computer science students?", "session_id": "test-session-1"}'
```

#### Reload Bot Configurations
```bash
curl -X POST http://localhost:8000/reload
```

## Document Processing System

The system includes a comprehensive document processing pipeline that allows you to upload, process, and search documents using vector embeddings. This integrates seamlessly with the DocumentSearchTool.

### Supported Document Formats

- **PDF files** (`.pdf`) - Using PyPDFLoader
- **Microsoft Word** (`.doc`, `.docx`) - Using Docx2txtLoader and UnstructuredWordDocumentLoader
- **Plain text** (`.txt`) - Using TextLoader with UTF-8 encoding

### Quick Start with Document Processing

1. **Upload documents** to the appropriate directory:
   ```bash
   # Place your documents in the data/raw directory
   cp your_document.pdf data/raw/academic/
   cp course_material.docx data/raw/student/
   ```

2. **Process documents** using the CLI script:
   ```bash
   # Process academic documents
   python scripts/process_documents.py process-dir "data/raw/academic" "academic_documents"

   # Process student materials
   python scripts/process_documents.py process-dir "data/raw/student" "student_documents"

   # Process a single file
   python scripts/process_documents.py process-file "data/raw/document.pdf" "my_collection"
   ```

3. **Verify processing**:
   ```bash
   # Check processing status
   python scripts/process_documents.py status

   # List available collections
   python scripts/process_documents.py list-collections

   # Search documents
   python scripts/process_documents.py search "artificial intelligence" "academic_documents"
   ```

4. **Update bot configuration** to use processed documents:
   ```yaml
   # In configs/academic_bot.yaml
   tools:
     - type: DocumentSearchTool
       enabled: true
       config:
         collection_name: "academic_documents"
         persist_directory: "./data/chroma_stores/academic_documents"
         embedding_model: "text-embedding-3-small"
         top_k: 10
   ```

### Document Processing Features

- **Automatic text chunking** with configurable chunk size and overlap
- **Vector embeddings** using OpenAI's text-embedding-3-small model
- **Metadata tracking** for processed documents
- **Batch processing** for multiple documents
- **Error handling** and comprehensive logging
- **Turkish character support** for document content and filenames
- **Integration** with existing DocumentSearchTool

### Directory Structure for Documents

```
data/
├── raw/                    # Upload your documents here
│   ├── academic/          # Academic papers and research
│   ├── student/           # Course materials and resources
│   ├── admin/             # Administrative documents
│   └── general/           # General purpose documents
├── processed/             # Processing metadata and logs
└── chroma_stores/         # Vector store collections
    ├── academic_documents/
    ├── student_documents/
    └── general_documents/
```

For detailed documentation, see [docs/DOCUMENT_PROCESSING.md](docs/DOCUMENT_PROCESSING.md).

## Bot Configuration

Bots are configured using YAML files in the `configs/` directory. Each bot has its own configuration file that specifies:

- Tools to use
- Database connections
- Prompt templates
- Agent configuration
- Metadata

Example configuration:

```yaml
name: StudentBot
description: A bot developed by Atlas University in Istanbul, Türkiye, designed to assist students with academic queries and research.

tools:
  - type: DocumentSearchTool
    enabled: true
    config:
      collection_name: student_documents
      persist_directory: ./chroma_db/student
      top_k: 5

  - type: MongoDBQueryTool
    enabled: true
    config:
      connection_string: mongodb://localhost:27017/
      database_name: student_db
      default_collection: courses
      max_results: 10
      model: gpt-4.1-mini
      temperature: 0.0

# ... more configuration ...

metadata:
  audience: students
  institution: Atlas University
  location: Istanbul, Türkiye
  languages:
    - English
    - Turkish
  topics:
    - course information
    - assignments
    - academic resources
    - research assistance
```

## Adding a New Bot

To add a new bot:

1. Create a new YAML configuration file in the `configs/` directory
2. Create prompt templates in the `prompts/` directory
3. Restart the application or call the `/reload` endpoint

No code changes are required to add a new bot!

## Extending the System

### Adding a New Tool

1. Create a new tool class in the `app/tools/` directory that inherits from `BaseTool`
2. Implement the `execute` method
3. Add the tool class to the `TOOL_CLASSES` dictionary in `app/core/agentic_rag.py`

### Customizing Prompts

Modify the prompt templates in the `prompts/` directory to customize the behavior of each bot.

## LLM-Based MongoDB Query Conversion

The system uses an LLM to convert natural language queries into MongoDB queries:

1. When a query is sent to the MongoDBQueryTool, the LLM analyzes the query and collection structure
2. The LLM generates a MongoDB query in JSON format that best matches the user's intent
3. The generated query is executed against the MongoDB database
4. Results are returned to the agent for further processing

This approach has several advantages:
- More accurate queries compared to simple text search
- Support for complex query operators ($eq, $gt, $lt, $in, $regex, etc.)
- Ability to handle queries in both English and Turkish
- Automatic adaptation to different collection schemas

Example configuration in the bot YAML file:

```yaml
- type: MongoDBQueryTool
  enabled: true
  config:
    connection_string: mongodb://localhost:27017/
    database_name: vector_db
    default_collection: usul_ve_esaslar-rag-chroma
    max_results: 10
    model: gpt-4.1-mini
    temperature: 0.0
```

Example natural language queries that get converted to MongoDB queries:

- "Find all documents about artificial intelligence"
- "Show me documents with page content containing the word 'university'"
- "Get documents where the metadata field 'source' contains 'research paper'"
- "Find documents from 2023 about machine learning"
- "Yapay zeka hakkında tüm belgeleri bul" (Turkish: "Find all documents about artificial intelligence")

## Self-RAG Implementation

The system uses a Self-RAG (Retrieval-Augmented Generation) approach to intelligently select which tools to use for each query:

1. When a query is received, the LLM analyzes the query and available tools
2. The LLM decides which tools are most relevant to answer the query
3. Only the selected tools are executed, improving efficiency and relevance
4. The agent then uses the results from these tools to generate a response

This approach has several advantages:
- More accurate tool selection compared to keyword-based approaches
- Reduced latency by only executing relevant tools
- Better responses by focusing on the most relevant information sources
- Ability to handle complex queries that don't contain obvious keywords

To test the Self-RAG implementation, run:

```
python test_self_rag.py
```

## Conversation Memory

The system includes short-term conversation memory that allows chatbots to maintain context across multiple interactions within a session:

1. Each conversation is associated with a unique `session_id` that identifies the conversation
2. The memory is ephemeral and only persists during the current session (no database storage)
3. The memory stores both user messages and AI responses
4. The memory is used to provide context for follow-up questions
5. The memory can be cleared at any time using the clear button in the UI or the API endpoint

### Using Conversation Memory in API Calls

To use conversation memory in API calls, include the same `session_id` in each request:

```bash
# First message in conversation
curl -X POST http://localhost:8000/bots/StudentBot/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What courses are available for computer science students?", "session_id": "my-conversation-1"}'

# Follow-up question using the same session_id
curl -X POST http://localhost:8000/bots/StudentBot/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Which of those has the highest enrollment?", "session_id": "my-conversation-1"}'
```

### Clearing Conversation Memory

To clear the memory for a specific session:

```bash
curl -X POST "http://localhost:8000/bots/StudentBot/clear-memory?session_id=my-conversation-1"
```

In PowerShell:

```powershell
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/bots/StudentBot/clear-memory?session_id=my-conversation-1"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see the LICENSE file for details.
