# Production GenAI MLOps Platform

A production-grade **LLM Gateway** built with FastAPI, demonstrating AI Platform Engineering, GenAI MLOps, and modern 2026 AI infrastructure practices.

## Architecture

This gateway sits between API consumers and LLM providers, enabling:

- **Provider Abstraction** — Swap between OpenAI, Azure OpenAI, and future providers without client changes
- **Observability** — Structured JSON logging, request tracing via `X-Request-ID`
- **Evaluation Gates** — Quality checks before promoting model versions (Phase 2+)
- **Blue-Green Deployment** — Safe rollouts with automated rollback (Phase 3+)

## Quick Start

### Prerequisites

- Python 3.11+
- An OpenAI API key

### Setup

```bash
# Clone and enter the project
cd "Production GenAI MLOps Platform"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Endpoints

| Method | Path            | Description                    |
|--------|-----------------|--------------------------------|
| GET    | `/health`       | Liveness probe                 |
| GET    | `/health/ready` | Readiness probe                |
| POST   | `/chat`         | OpenAI-compatible chat         |
| GET    | `/docs`         | Swagger UI (dev only)          |

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Chat completion
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

### Run Tests

```bash
pytest tests/ -v
```

### Docker

```bash
docker compose up --build
```

## Project Structure

```
app/
├── config.py                  # Pydantic Settings
├── logging_config.py          # Structured JSON logging
├── main.py                    # FastAPI app factory
├── api/
│   ├── routes/
│   │   ├── health.py          # Health probes
│   │   └── chat.py            # Chat endpoint
│   └── middleware/
│       └── request_id.py      # X-Request-ID
├── models/
│   ├── requests.py            # Request schemas
│   └── responses.py           # Response schemas
└── services/
    ├── llm_service.py          # High-level LLM service
    └── providers/
        ├── base.py             # BaseProvider ABC
        └── openai_provider.py  # OpenAI implementation
```

## Tech Stack

- **FastAPI** — Async API framework
- **Pydantic v2** — Data validation + settings
- **OpenAI SDK** — LLM provider client
- **python-json-logger** — Structured logging
- **Docker** — Containerization

## License

Private — All rights reserved.
