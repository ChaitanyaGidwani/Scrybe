# Scrybe 🦅

### Autonomous Multi-Agent Web Intelligence & Market Synthesis System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Protocol: A2A v1.0](https://img.shields.io/badge/Protocol-A2A%20v1.0-blueviolet.svg)](#a2a-protocol-architecture)
[![Tests: 116+](https://img.shields.io/badge/Tests-116%20passing-brightgreen.svg)](#verification)
[![Architecture: Multi-Agent](https://img.shields.io/badge/Architecture-6--Agent%20Pipeline-green.svg)](#-the-six-autonomous-agents)
[![Compliance: GDPR EDPB 03/2026](https://img.shields.io/badge/Compliance-GDPR%20EDPB%2003%2F2026-purple.svg)](docs/02_LEGAL_COMPLIANCE_AND_ETHICS_FRAMEWORK.md)

> **Scrybe turns raw, messy web data into decision-ready market intelligence—automatically, compliantly, and with zero hallucinations.**

---

## 🎯 Executive Overview

Modern competitive intelligence is broken. Organizations spend thousands of analyst hours manually checking competitor pricing tables and documentation, or pay $20,000–$50,000+ for legacy tools (Klue, Crayon) that still require heavy manual curation. Meanwhile, pixel-diff trackers (Visualping) fire dozens of false-alarm notifications a week, causing **up to 40% of teams to churn within 12 months due to alert fatigue**.

**Scrybe solves this with an autonomous 6-agent pipeline.**  
Instead of dumping raw HTML diffs, Scrybe autonomously crawls public pricing and feature pages, strictly verifies data against source DOM elements, cross-corroborates macro trends across ≥2 independent competitors, and generates cited executive intelligence briefs.

---

## 📚 Complete Project Documentation Suite

All research, compliance frameworks, architectural blueprints, and financial models are organized in [`docs/`](docs/):

| Document | Purpose & Key Topics |
| :--- | :--- |
| 📊 [**01. Market Research & Vertical Strategy**](docs/01_MARKET_RESEARCH_AND_VERTICAL_STRATEGY.md) | Competitive intelligence market sizing ($4.1B TAM), 40% churn analysis, beachhead selection (**B2B AI Developer Tooling & APIs**), buyer personas (PMMs, Founders), and monetization model. |
| ⚖️ [**02. Legal, Compliance & Ethics Framework**](docs/02_LEGAL_COMPLIANCE_AND_ETHICS_FRAMEWORK.md) | hiQ v. LinkedIn & Meta v. Bright Data legal precedents, EU GDPR & EDPB Guidelines 03/2026, legitimate interest 3-part test, automated `robots.txt` enforcement, and regex/NER PII redactor. |
| 🏗️ [**03. System Architecture & Agent Spec**](docs/03_SYSTEM_ARCHITECTURE_AND_AGENT_SPEC.md) | Multi-agent sequential state machine, `ScrybeState` data contracts, 6 agent deep-dives, tiered scraping (`httpx` → `curl_cffi` → `Crawl4AI`), and circuit breaker recovery. |
| 📐 [**04. Data Schemas & Prompt Engineering**](docs/04_DATA_SCHEMAS_AND_PROMPT_ENGINEERING.md) | Production Pydantic models, strict `null` anti-hallucination rules, prompt templates for extraction, multi-source corroboration, self-healing selectors, and Reflexion repairs. |
| 🗺️ [**05. Implementation Blueprint & Roadmap**](docs/05_IMPLEMENTATION_BLUEPRINT_AND_ROADMAP.md) | 6-week engineering execution roadmap (Milestones M1–M6), daily task breakdown, test strategy, Docker/Postgres migration path, and acceptance criteria. |
| 💰 [**06. Feasibility & LLM Unit Economics**](docs/06_FEASIBILITY_AND_LLM_ECONOMICS.md) | Tiered hybrid LLM strategy (cheap models for extraction, frontier models for synthesis), token cost per run ($0.13), customer ROI (160% in Month 1), and >90% gross margin model. |

---

## 🏛️ Architecture Overview

```mermaid
flowchart TD
    Config["config/sources.yaml"] --> Orchestrator["A2A Pipeline Orchestrator"]
    
    subgraph INGESTION ["1. Ingestion & Compliance Layer"]
        Orchestrator --> CompPre["Compliance Agent: Pre-Flight Gate"]
        CompPre -- "Disallowed" --> AuditHalt["Log Audit & Halt Domain"]
        CompPre -- "Approved" --> Reader["Reader Agent (Tier 1 -> Tier 2 -> Tier 3)"]
        Reader --> CompPost["Compliance Agent: PII Redaction"]
    end
    
    subgraph EXTRACTION ["2. Structured Extraction Layer"]
        CompPost --> Analyst["Analyst Agent (Pydantic Schema)"]
        Analyst --> ConfCheck{"Confidence >= 0.60?"}
        ConfCheck -- "Below 0.60" --> ReviewGate["Reflexion / Human Review Gate"]
        ConfCheck -- "Verified" --> FAISS[("FAISS Vector Index (Delta Detection)")]
    end
    
    subgraph STRATEGY ["3. Synthesis & Corroboration Layer"]
        FAISS --> Strategist["Strategist Agent (The 2-Source Corroborator)"]
        Strategist --> TwoSource{"Corroborated >= 2 Sources?"}
        TwoSource -- "Single Source" --> CompanyAction["Flagged as Isolated Move"]
        TwoSource -- ">= 2 Sources" --> MacroTrend["Synthesized Macro Market Shift"]
    end
    
    subgraph PUBLISHING ["4. Multi-Channel Publishing"]
        MacroTrend --> Formatter["Formatter Agent"]
        CompanyAction --> Formatter
        Formatter --> MD["Executive Markdown Report"]
        Formatter --> PDF["Styled PDF (ReportLab)"]
        Formatter --> API["FastAPI JSON Payload / WebSocket"]
    end
```

---

## 🔗 A2A Protocol Architecture

Scrybe agents communicate via the **Agent-to-Agent (A2A) v1.0 protocol** — an open, decoupled standard for multi-agent coordination using JSON-RPC 2.0:

| Component | File | Purpose |
| :--- | :--- | :--- |
| **Data Models** | `scrybe/a2a/models.py` | `AgentCard`, `Task`, `Message`, `Artifact`, `TaskState`, JSON-RPC types |
| **Server** | `scrybe/a2a/server.py` | Base HTTP server with JSON-RPC 2.0 dispatch (`agent/sendMessage`, `tasks/get`, `tasks/cancel`) |
| **Client** | `scrybe/a2a/client.py` | Async HTTP client with SSE event stream parsing |
| **Registry** | `scrybe/a2a/registry.py` | In-memory and remote agent card registration, lookup by skill/tag |
| **Agent Wrappers** | `scrybe/agents/a2a_wrappers.py` | A2A server wrappers and cards for all 6 agents (ports 8010–8015) |
| **Orchestrator** | `scrybe/a2a/orchestrator.py` | Pipeline orchestrator supporting `in_process` and `remote` execution modes |

**Execution Modes:**
- **`in_process`** (default): All agents run in one process — handler calls are direct, zero HTTP overhead. Ideal for development and single-machine deployments.
- **`remote`**: Each agent runs as a separate HTTP service, discovered via Agent Cards. Enables horizontal scaling across machines.

---

## 🤖 The Six Autonomous Agents

| Agent | Port | Responsibility | Core Technology |
| :--- | :---: | :--- | :--- |
| **Compliance Agent** | 8010 | Enforces `robots.txt`, `ai.txt`, rate limits, and scrubs PII from all ingested raw data. | `urllib.robotparser`, Regex |
| **Reader Agent** | 8011 | Executes tiered crawling (`httpx` → `curl_cffi` → `Playwright`), converting DOM into clean Markdown. | `httpx`, `curl_cffi`, `Playwright` |
| **Analyst Agent** | 8012 | Normalizes token pricing and extracts structured pricing tiers with confidence scoring. | Pydantic v2, Constrained Decoder |
| **Memory & Reflexion** | 8013 | Maintains rolling buffer, executes Reflexion critique loops, and detects semantic deltas via FAISS. | FAISS, Reflexion (`arXiv:2303.11366`) |
| **Strategist Agent** | 8014 | Evaluates price deltas, enforces the 2-source corroboration rule, and writes sales battlecards. | Frontier LLM (Claude 3.5 / GPT-4o) |
| **Formatter Agent** | 8015 | Compiles verified intelligence into publication-quality Markdown briefs and PDF reports. | `ReportLab`, `python-docx` |

---

## 📊 Datasets & Evaluation

Scrybe uses a multi-tiered dataset architecture:

| Dataset | Source | Purpose |
| :--- | :--- | :--- |
| **Golden Benchmark** | `scrybe/tools/benchmark_catalog.py` | 6 hand-verified AI platforms (OpenAI, Anthropic, Groq, Together AI, Mistral, Pinecone) with exact DOM snippets and target pricing tiers |
| **Live OpenRouter Catalog** | `https://openrouter.ai/api/v1/models` | 60+ provider real-time pricing with automatic per-token → per-1M normalization |
| **Fine-Tuning Dataset** | `data/training/` | ChatML/Alpaca JSONL with adversarial negatives for training SLMs (Qwen-2.5-7B / Llama-3.1-8B) |
| **Evaluation Harness** | `scrybe/tools/evaluation_harness.py` | Precision, recall, F1, DOM grounding ratio, and hallucination rate metrics |

```bash
# View the golden benchmark catalog
PYTHONPATH=. uv run python cli.py dataset --catalog

# Fetch live pricing from OpenRouter API
PYTHONPATH=. uv run python cli.py dataset --fetch-openrouter

# Export fine-tuning dataset (ChatML format)
PYTHONPATH=. uv run python cli.py dataset --export-finetuning --output data/training/scrybe.jsonl

# Run quantitative evaluation harness
PYTHONPATH=. uv run python cli.py evaluate --tolerance 0.05
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ (recommended: 3.11)
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
- Node.js 20+ (for frontend development only)
- Docker & Docker Compose (optional, for containerized deployment)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/ChaitanyaGidwani/Scrybe.git
cd Scrybe

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your LLM API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
```

### 3. Verification
```bash
# Run 116+ unit, integration, and end-to-end tests
PYTHONPATH=. uv run pytest tests/ -v
```

### 4. Running Scrybe

#### A2A Multi-Agent Pipeline (Recommended)
```bash
# Run pipeline using A2A protocol (in-process mode)
PYTHONPATH=. uv run python cli.py run --a2a

# Run pipeline in distributed remote A2A mode
PYTHONPATH=. uv run python cli.py run --a2a --mode remote
```

#### Launch the API Server + Dashboard
```bash
# Start the unified FastAPI backend (serves React SPA + WebSocket + REST)
PYTHONPATH=. uv run python cli.py api --port 8000
```
Then navigate to `http://localhost:8000` for the full dashboard.

#### Frontend Development Mode
```bash
# Start Vite React dev server with HMR
cd frontend && npm install && npm run dev
```

### 5. Docker Deployment
```bash
# Build and run with Docker Compose
docker compose up --build -d

# View logs
docker compose logs -f scrybe
```

---

### 6. Project Directory Layout
```
Scrybe/
├── scrybe/                 # Core Python package
│   ├── a2a/                # A2A Protocol v1.0 Core Layer
│   │   ├── models.py       # AgentCard, Task, Message, Artifact, TaskState
│   │   ├── server.py       # Base A2A HTTP server & JSON-RPC dispatcher
│   │   ├── client.py       # A2A client with SSE streaming support
│   │   ├── registry.py     # Local & remote Agent Card discovery
│   │   └── orchestrator.py # A2A-powered autonomous pipeline orchestrator
│   ├── agents/             # The 6 autonomous agents + A2A wrappers
│   │   ├── compliance.py   # Pre-flight & PII redactor
│   │   ├── reader.py       # Tiered crawler (httpx -> curl_cffi -> Playwright)
│   │   ├── analyst.py      # Structured extraction & Reflexion self-repair
│   │   ├── memory.py       # Buffer, Reflexion, FAISS vector store
│   │   ├── strategist.py   # Multi-source corroboration (≥2 sources)
│   │   ├── formatter.py    # Markdown & PDF generation
│   │   └── a2a_wrappers.py # A2A Agent Card wrappers for all 6 agents
│   ├── api/                # FastAPI application
│   │   ├── main.py         # Endpoints, SPA static mount & WebSocket hub
│   │   ├── routes.py       # Pricing matrix, audits, insights, reports
│   │   └── websocket.py    # Real-time pipeline event broadcasting
│   ├── tools/              # Extraction, validation, and refinement
│   │   ├── benchmark_catalog.py  # Golden benchmark + OpenRouter ingest
│   │   ├── constrained_decoder.py # DOM grounding & price normalization
│   │   ├── evaluation_harness.py  # Precision/recall/F1 evaluation
│   │   ├── finetuning.py          # ChatML/Alpaca export + QLoRA scripts
│   │   ├── llm_client.py          # Unified OpenAI/Anthropic/Google client
│   │   ├── extractor.py           # HTML cleaning & prompt builder
│   │   ├── validator.py           # Confidence scoring & cross-field sanity
│   │   ├── reporter.py            # Markdown & PDF report generator
│   │   └── scraper.py             # Tier 1 HTTP scraper
│   ├── storage/            # Pydantic models & SQLite/Postgres engine
│   │   ├── models.py       # ScrybeState, CompetitorProductRecord, etc.
│   │   └── db.py           # DatabaseManager (SQLAlchemy Core)
│   └── memory/             # Vector store & rolling buffer
│       ├── buffer.py       # RollingBuffer with eviction
│       ├── reflection.py   # Reflexion loop (arXiv:2303.11366)
│       └── vector_store.py # FAISS wrapper
├── frontend/               # Modern React + Vite Dashboard
│   └── src/
│       ├── components/     # AgentTopology, PipelineTerminal, MatrixView, etc.
│       ├── App.jsx         # Live WebSocket listener, state sync, view tabs
│       └── index.css       # Obsidian dark theme, glassmorphism, pulse animations
├── config/                 # Configuration
│   ├── settings.py         # Pydantic-settings with typed env vars
│   └── sources.yaml        # Target web sources & scraping config
├── data/training/          # Fine-tuning datasets & Unsloth scripts
├── docs/                   # Comprehensive research & architecture specs
├── tests/                  # 116+ automated tests (unit + integration + E2E)
├── cli.py                  # CLI entry point (run, api, dashboard, dataset, evaluate)
├── Dockerfile              # Multi-stage build (Node frontend + Python runtime)
├── docker-compose.yml      # Unified deployment with Redis
├── pyproject.toml          # PEP 621 project metadata
└── requirements.txt        # Flat dependency list
```

---

## 📅 Roadmap & Milestones

- [x] **Phase 0:** Market Research, Compliance Framework & Architecture Specification.
- [x] **Milestone 1:** Ingestion Foundation & Compliance Guard (`httpx` + `robots.txt` + SQLite).
- [x] **Milestone 2:** Tiered Scraping (`curl_cffi` + `Playwright` + self-healing parser).
- [x] **Milestone 3:** Analyst Agent & Schema Extraction with confidence gating.
- [x] **Milestone 4:** Strategist Agent & Publication Engine (Multi-source + Markdown/PDF).
- [x] **Milestone 5:** Memory & Reflexion Layer (Rolling buffer + FAISS semantic deltas).
- [x] **Milestone 6:** A2A Protocol Integration, FastAPI endpoints, React dashboard & WebSocket streaming.
- [x] **Milestone 7:** Benchmark datasets, constrained decoding, fine-tuning pipeline & evaluation harness.
- [x] **Milestone 8:** End-to-end pipeline integration tests, Docker containerization & project finalization.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.