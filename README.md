---
title: My Agents
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.16.0
app_file: app.py
pinned: false
---

# My Agents — Personal AI Digital Twin

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![Gradio](https://img.shields.io/badge/Gradio-6.16-orange?logo=gradio)](https://gradio.app)
[![HF Spaces](https://img.shields.io/badge/HuggingFace-Spaces-yellow?logo=huggingface)](https://huggingface.co/spaces)

An AI agent that acts as a personal digital twin — representing you on your website, answering questions about your career and background, capturing leads, and escalating knowledge gaps. Powered by any OpenAI-compatible model (GPT, Gemini, Llama) with a built-in LLM evaluator that self-corrects low-quality responses before they reach the user.

---

## How It Works

```
User Message
     │
     ▼
┌─────────────────────────────────┐
│           Me (Agent)            │
│                                 │
│  1. Build prompt from           │
│     profile (PDF + summary)     │
│                                 │
│  2. Agentic loop (max 5x)       │
│     ├── LLM call                │
│     └── Tool calls              │
│         ├── record_user_details │
│         └── record_unknown_question │
│                                 │
│  3. Evaluator LLM grades reply  │
│     ├── Pass → return reply     │
│     └── Fail → rerun with       │
│         feedback injected       │
└─────────────────────────────────┘
     │
     ▼
Gmail notification (leads + unknown questions)
```

---

## Features

| Feature | Detail |
|---------|--------|
| **Digital Twin** | Responds in-character using your summary and LinkedIn profile as context |
| **Multi-model** | Swap between OpenAI GPT, Google Gemini, or local Ollama/Llama with a single env var |
| **Agentic Loop** | Up to 5 tool-call iterations per message before settling on a reply |
| **Self-Evaluation** | A second LLM judges every response; failed responses are automatically re-generated with feedback |
| **Lead Capture** | Agent asks for visitor email and records it via Gmail notification |
| **Gap Tracking** | Unknown questions are logged and emailed so you can improve the agent over time |
| **Structured Logging** | Per-request `conversation_id`, LLM latency, token usage via `structlog` |
| **Optional Auth** | Lock the Gradio UI behind username/password via env vars |

---

## Project Structure

```
my-agents/
├── app.py                  # Gradio ChatInterface entry point
├── config.py               # Multi-provider OpenAI client factory
├── logger.py               # structlog configuration
├── requirements.txt        # Python dependencies
├── agent/
│   ├── chat.py             # Me class — agentic loop + evaluation
│   ├── evaluate.py         # Evaluator LLM + rerun logic
│   ├── prompts.py          # System, evaluator, and user prompts
│   └── tools.py            # Tool definitions + registry
├── data/
│   └── loader.py           # Loads profile from PDF + summary.txt
├── notifications/
│   └── email.py            # Gmail SMTP notification
└── sample-data/
    ├── profile.pdf          # LinkedIn PDF export
    └── summary.txt          # Free-text professional summary
```

---

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- API key for at least one supported model provider
- Gmail account with an [App Password](https://myaccount.google.com/apppasswords) for notifications

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/nirajs-code/my-agents.git
cd my-agents

# 2. Install dependencies
uv sync
# or: pip install -r requirements.txt

# 3. Add your profile data
cp your-linkedin-export.pdf sample-data/profile.pdf
# Edit sample-data/summary.txt with your professional summary

# 4. Configure environment
cp .env.example .env
# Fill in your API keys and settings

# 5. Run
python app.py
```

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `MODEL` | Yes | Model ID — e.g. `gpt-4o-mini`, `gemini-2.5-flash` |
| `EVAL_MODEL` | No | Evaluator model (defaults to `MODEL`) |
| `OPENAI_API_KEY` | If using GPT | OpenAI API key |
| `GOOGLE_API_KEY` | If using Gemini | Google AI Studio API key |
| `GEMINI_BASE_URL` | If using Gemini | Gemini OpenAI-compat base URL |
| `OLLAMA_API_KEY` | If using Ollama | Set to `ollama` |
| `OLLAMA_BASE_URL` | If using Ollama | `http://localhost:11434/v1` |
| `GMAIL_USER` | Yes | Gmail address for sending notifications |
| `GMAIL_APP_PASSWORD` | Yes | Gmail App Password |
| `GMAIL_TO` | Yes | Destination email for lead/gap alerts |
| `PROFILE_NAME` | Yes | Your full name — injected into all prompts |
| `GRADIO_SHARE` | No | `true` to create a public share link |
| `GRADIO_USERNAME` | No | Enables basic auth on the UI |
| `GRADIO_PASSWORD` | No | Required if `GRADIO_USERNAME` is set |

---

## Supported Models

| Provider | Example `MODEL` value | Notes |
|----------|-----------------------|-------|
| OpenAI | `gpt-4o-mini`, `gpt-4o` | Set `OPENAI_API_KEY` |
| Google Gemini | `gemini-2.5-flash` | Set `GOOGLE_API_KEY` + `GEMINI_BASE_URL` |
| Ollama (local) | `llama3.2:1b` | Not available on HF Spaces |

---

## Deployment — Hugging Face Spaces

1. [Create a new Space](https://huggingface.co/new-space) — select **Gradio** SDK
2. Add all env vars under **Settings → Variables and secrets**
3. Push this repo to the Space:

```bash
git remote add hf https://YOUR_HF_USERNAME:$HF_TOKEN@huggingface.co/spaces/YOUR_HF_USERNAME/YOUR_SPACE_NAME
git push hf main
```

---

## CI/CD — GitHub Actions

Create `.github/workflows/deploy.yml` to auto-deploy on every push to `main`: