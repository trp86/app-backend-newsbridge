# NewsBridge Backend

Python-based backend for news aggregation, processing, and translation.

## Features

- RSS feed ingestion from multiple sources
- Deduplication using content hashing
- AI-powered summarization (30/111/250 words)
- Translation to Odia
- SQLite database storage
- Editorial quality filtering

## Tech Stack

- Python 3.12
- uv (package manager)
- Pydantic (data validation)
- feedparser (RSS parsing)
- OpenRouter API (LLM integration)
- SQLite (database)

## Setup

### Option 1: Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### Option 2: Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
# or
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov pytest-asyncio ruff mypy
```

### Initialize Database

```bash
# Create database and schema
python scripts/init_db.py

# Run tests
pytest
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
OPENROUTER_API_KEY=your_api_key_here
DATABASE_PATH=data/newsbridge.db
LOG_LEVEL=INFO
```

## Project Structure

```
backend/
├── src/
│   ├── core/        # Config, database, schemas
│   ├── ingestion/   # RSS collection, parsing
│   ├── editorial/   # Summarization, filtering
│   ├── translation/ # Odia translation
│   └── storage/     # Database repositories
├── tests/           # Unit tests
├── scripts/         # Utility scripts
└── data/            # Database and schema
```

## Usage

```python
# Test ingestion
python scripts/test_ingestion.py

# Test editorial pipeline
python scripts/test_editorial.py

# Test translation
python scripts/test_translation.py
```
