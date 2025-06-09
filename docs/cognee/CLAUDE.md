# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cognee is a library for enriching LLM context with a semantic layer for better understanding and reasoning. It provides memory for AI agents in just 5 lines of code, using scalable, modular ECL (Extract, Cognify, Load) pipelines to build dynamic memory and replace RAG systems.

## Common Development Commands

```bash
# Install with UV (recommended for development)
uv sync --all-extras

# Install with pip
pip install -e .

# Install specific extras
pip install -e ".[api,dev,postgres,neo4j]"

# Run tests
python cognee/cognee/tests/test_library.py
pytest cognee/tests/

# Run the API server
uvicorn cognee.api.client:app --reload

# Run linting and formatting
ruff check .
ruff format .

# Run pre-commit hooks
pre-commit run --all-files

# Run database migrations
alembic upgrade head

# Check package structure
./tools/check-package.sh

# Run the GUI
python cognee-gui.py
```

## High-Level Architecture

The application follows an ECL (Extract, Cognify, Load) pipeline architecture:

1. **Core API** (`cognee/api/v1/`):
   - `add` - Add data to cognee (text, documents, images, audio)
   - `cognify` - Process data to create knowledge graphs
   - `search` - Query the knowledge graph with different search types
   - `delete` - Remove data from the system
   - `prune` - Clean up data and system state
   - `visualize` - Visualize the knowledge graph

2. **Modules** (`cognee/modules/`):
   - `ingestion` - Data ingestion from 30+ sources
   - `chunking` - Text chunking and processing
   - `cognify` - Core knowledge graph generation
   - `graph` - Graph database operations
   - `retrieval` - Data retrieval mechanisms
   - `search` - Search implementations
   - `storage` - Storage abstractions
   - `engine` - Pipeline execution engine
   - `ontology` - Ontology management
   - `users` - User management with FastAPI Users

3. **Infrastructure** (`cognee/infrastructure/`):
   - Database adapters (PostgreSQL, Neo4j, Weaviate, Qdrant, etc.)
   - Vector database interfaces
   - Graph database interfaces
   - LLM integrations (OpenAI, Anthropic, Gemini, Ollama, etc.)

4. **Tasks** (`cognee/tasks/`):
   - Entity extraction and completion
   - Summarization
   - Graph operations
   - Temporal awareness
   - Ingestion tasks

## Key Design Patterns

- **Async-First**: All core operations are async using asyncio
- **Modular Pipeline**: ECL pipeline with pluggable components
- **Multi-Database Support**: Abstractions for various vector and graph databases
- **Provider Agnostic**: Support for multiple LLM providers through litellm
- **Pydantic Models**: Type-safe data models throughout
- **FastAPI Integration**: RESTful API with automatic documentation

## Development Setup

1. **Environment Variables** (create `.env` from `.env.template`):
   ```
   LLM_API_KEY=your_openai_api_key
   ENVIRONMENT=dev
   DEBUG=true
   ```

2. **Database Setup**:
   - Default uses SQLite for development
   - PostgreSQL recommended for production
   - Run migrations: `alembic upgrade head`

3. **Optional Dependencies**:
   - `api` - FastAPI server components
   - `postgres` - PostgreSQL support
   - `neo4j` - Neo4j graph database
   - `weaviate` - Weaviate vector database
   - `notebook` - Jupyter notebook support
   - `dev` - Development tools

## Testing

- Unit tests in `cognee/tests/unit/`
- Integration tests in `cognee/tests/`
- Run specific test: `pytest cognee/tests/test_library.py::test_name`
- Test coverage: `pytest --cov=cognee`

## Code Style

- Formatter: Ruff (configured in `pyproject.toml`)
- Line length: 100 characters
- Pre-commit hooks configured for consistency
- Type hints required for all public APIs

## Common Workflows

### Adding New Data Sources
1. Implement adapter in `cognee/modules/ingestion/`
2. Register in data source registry
3. Add tests for new adapter

### Creating Custom Pipelines
1. Define pipeline tasks in `cognee/tasks/`
2. Configure pipeline in `cognee/modules/pipelines/`
3. Expose through API if needed

### Adding LLM Providers
1. Configure in `cognee/infrastructure/llm/`
2. Add to litellm configuration
3. Update environment template

## Architecture Notes

- **ECL Pipeline**: Extract → Cognify → Load pattern for all data processing
- **Knowledge Graph**: Central to the system, stores entities and relationships
- **Vector Storage**: For semantic search capabilities
- **Multi-Modal**: Supports text, images, audio, and documents
- **Scalable**: Designed for both small and large-scale deployments

## Debugging Tips

- Enable debug mode: `DEBUG=true` in environment
- Check logs in `logs/` directory
- Use structured logging with `cognee.shared.logging_utils.get_logger()`
- FastAPI docs available at `/docs` when running the API

## Important Files

- `cognee/__init__.py` - Main API exports
- `cognee/api/client.py` - FastAPI application setup
- `cognee/modules/cognify/cognify.py` - Core cognify logic
- `cognee/base_config.py` - Configuration management
- `pyproject.toml` - Project dependencies and configuration