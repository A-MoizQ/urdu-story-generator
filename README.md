# Ur## Architecture

```
┌──────────────────┐     SSE stream     ┌────────────────────┐    HTTP/SSE       ┌─────────────────────────────────────┐
│  Browser (React) │ ◄────────────────► │  Next.js API Route │ ◄───────────────► │  Docker Container (Render)          │
│  (Vercel)        │                    │  (Vercel)          │                   │  ┌─────────────────────────────┐    │
└──────────────────┘                    └────────────────────┘                   │  │ HTTP Gateway (FastAPI/SSE)  │    │
                                                                                │  │ port 10000 (public)         │    │
                                                                                │  └──────────┬──────────────────┘    │
                                                                                │             │ in-process            │
                                                                                │  ┌──────────▼──────────────────┐    │
                                                                                │  │ gRPC Server                 │    │
                                                                                │  │ port 50051 (internal)       │    │
                                                                                │  └──────────┬──────────────────┘    │
                                                                                │             │                       │
                                                                                │  ┌──────────▼──────────────────┐    │
                                                                                │  │ Inference Engine            │    │
                                                                                │  │ (BPE Tokenizer + Trigram)   │    │
                                                                                │  └─────────────────────────────┘    │
                                                                                └─────────────────────────────────────┘
```

**Why two protocols?**
- **gRPC** (port 50051): Used for direct clients (grpcurl, testing, local dev). Assignment requirement.
- **HTTP/SSE** (port 10000): Render's load balancer terminates TLS and forwards HTTP. The Next.js frontend on Vercel calls this endpoint. SSE streams tokens to the browser just like ChatGPT.ration AI — Backend Microservice

An AI-powered Urdu story generator for children, built with a trigram language model and BPE tokenizer, served via gRPC streaming.

## Architecture

```
┌──────────────────┐     SSE stream     ┌────────────────────┐    gRPC stream    ┌─────────────────────┐
│  Browser (React) │ ◄────────────────► │  Next.js API Route │ ◄───────────────► │  gRPC Backend       │
│  (Vercel)        │                    │  (Vercel)          │                   │  (Render / Docker)  │
└──────────────────┘                    └────────────────────┘                   └─────────────────────┘
                                                                                  ├── tokenizer/  (BPE)
                                                                                  ├── model/      (Trigram LM)
                                                                                  ├── inference/  (Generator)
                                                                                  ├── server/     (gRPC)
                                                                                  └── models/     (Artifacts)
```

## Project Structure

```
assignment1/
├── backend/
│   ├── proto/                  # gRPC protobuf definitions
│   │   └── story.proto
│   ├── server/                 # gRPC server implementation
│   │   └── main.py
│   ├── gateway/                # HTTP/SSE gateway (FastAPI)
│   │   └── __init__.py
│   ├── tokenizer/              # BPE tokenizer (placeholder)
│   │   └── __init__.py
│   ├── model/                  # Trigram language model (placeholder)
│   │   └── __init__.py
│   ├── inference/              # Generation pipeline
│   │   └── __init__.py
│   ├── models/                 # Trained artifacts (.json files)
│   ├── scripts/
│   │   └── generate_proto.sh   # Proto stub generation
│   ├── tests/
│   │   ├── test_server.py      # gRPC server tests
│   │   └── test_gateway.py     # HTTP gateway tests
│   ├── config.py               # Environment-based configuration
│   ├── entrypoint.py           # Unified entrypoint (gRPC + HTTP)
│   ├── Dockerfile              # Multi-stage production build
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # Lint → Test → Build → Deploy
├── render.yaml                 # Render IaC blueprint
└── README.md
```

## Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- Docker (optional, for container testing)

### 1. Set up virtual environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate proto stubs

```bash
bash scripts/generate_proto.sh
```

### 3. Run the server

```bash
cd ..  # back to repo root
python -m backend.server.main
```

The gRPC server will start on `0.0.0.0:50051`.

### 4. Test with grpcurl

```bash
# Health check
grpcurl -plaintext localhost:50051 story.StoryGenerator/HealthCheck

# Generate story (streaming)
grpcurl -plaintext -d '{"prefix": "ایک دفعہ", "max_length": 20}' \
  localhost:50051 story.StoryGenerator/GenerateStory
```

### 5. Run tests

```bash
python -m pytest backend/tests/ -v
```

## Docker

### Build

```bash
cd backend
docker build -t urdu-story-backend .
```

### Run

```bash
docker run -p 50051:50051 urdu-story-backend
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs on every push/PR to `main`:

| Stage | Trigger | What it does |
|-------|---------|--------------|
| **Lint** | Push & PR | Runs `ruff` linter |
| **Test** | Push & PR | Generates proto stubs, runs `pytest` |
| **Build** | Push only | Builds Docker image, pushes to GHCR |
| **Deploy** | Push only | Triggers Render deploy webhook |

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `RENDER_DEPLOY_HOOK_URL` | Deploy hook URL from Render Dashboard → Service → Settings |

## Deployment (Render)

1. Connect your GitHub repo to [Render](https://render.com).
2. Render auto-detects `render.yaml` and creates the service.
3. Set the deploy hook URL as a GitHub secret.
4. Every push to `main` → CI tests → Docker build → auto-deploy.

## Plugging in the Real Tokenizer & Model

Your teammates need to:

1. **BPE Tokenizer** (`backend/tokenizer/__init__.py`):
   - Implement `encode(text) → list[int]` with BPE merge logic.
   - Save the trained tokenizer as `models/bpe_tokenizer.json` with schema:
     ```json
     { "vocab": {"token": id, ...}, "merges": [["a", "b"], ...] }
     ```

2. **Trigram Model** (`backend/model/__init__.py`):
   - Implement `get_distribution(t1, t2) → dict[int, float]` with interpolation.
   - Save the trained model as `models/trigram_model.json` with schema:
     ```json
     {
       "trigram_counts": {"t1,t2,t3": count, ...},
       "bigram_counts": {"t1,t2": count, ...},
       "unigram_counts": {"t1": count, ...},
       "lambdas": [0.1, 0.3, 0.6],
       "vocab_size": 250
     }
     ```

3. Place artifact files in `backend/models/` and commit them.

The server will automatically detect and load them on next deploy.

## gRPC API Reference

### `GenerateStory` (server-streaming)

**Request:**
```
{ "prefix": "ایک دفعہ", "max_length": 100 }
```

**Streamed Response (one per token):**
```
{ "token": "کا", "is_finished": false, "full_text": "ایک دفعہ کا" }
```

### `HealthCheck` (unary)

**Response:**
```
{ "status": "healthy", "model_loaded": "True", "tokenizer_loaded": "True" }
```
