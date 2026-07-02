<div align="center">

# 🔍 Job Matcher

**An AI-powered job search assistant that parses your resume, matches it to relevant job listings using semantic search, generates tailored cover letters, and notifies you of top matches — through a multi-agent pipeline you can watch work in real time.**

[![Live App](https://img.shields.io/badge/Live%20App-Open-brightgreen)](https://aryanrajnitagartala-ai--job-search-service-web-ui.modal.run/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Deployment](https://img.shields.io/badge/Deployed%20on-Modal-orange)](https://modal.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#license)

</div>

<br>

![Job Matcher Demo](https://raw.githubusercontent.com/aryanrajnitagartala-ai/Multi-Agent_AI_Resume_Copilot/main/Screenshot%202026-07-02%20125537.png)

<div align="center">

**Paste your resume → Find matching jobs → Generate cover letters → Get notifications**

</div>

<br>

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Running Locally](#running-locally)
- [Deploying to Modal](#deploying-to-modal)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [API Access](#api-access)
- [Author](#author)
- [License](#license)

<br>

## Features

| | |
|---|---|
| 📄 **Resume Parsing** | Extracts name, email, skills, years of experience, job titles, education, and a background summary from raw resume text |
| 🔎 **Semantic Job Matching** | Uses RAG (ChromaDB + sentence-transformers) to retrieve candidate jobs, then an LLM re-ranks and scores them against your profile |
| ✉️ **Cover Letter Generation** | Generates a tailored, ready-to-send cover letter for any matched job |
| 🔔 **Push Notifications** | Sends a Pushover alert automatically when a match scores 80%+ (falls back to a dry-run log if credentials aren't set) |
| 🤖 **Live Agent Activity Log** | A real-time, color-coded log panel shows each agent's steps as the pipeline runs |
| 🇮🇳 **Curated Dataset** | 100 Indian company job listings with ₹ LPA salary ranges |

<br>

## Architecture

A multi-agent pipeline, with each agent owning a single responsibility:

```
                         Resume Text
                              │
                              ▼
                  ┌───────────────────────┐
                  │      Resume Agent      │   Parses resume → structured ResumeProfile
                  └───────────┬───────────┘
                              ▼
                  ┌───────────────────────┐
                  │    Job Match Agent      │   RAG search (ChromaDB) → LLM re-ranks top matches
                  └───────────┬───────────┘
                              ▼
                  ┌───────────────────────┐
                  │  Cover Letter Agent     │   Generates a tailored cover letter for the best match
                  └───────────┬───────────┘
                              ▼
                  ┌───────────────────────┐
                  │  Notification Agent     │   Sends a Pushover alert for 80%+ matches (or dry-run)
                  └───────────────────────┘
```

| Agent | File | Purpose |
|---|---|---|
| `ResumeAgent` | `agents/resume_agent.py` | Parses resume text into a structured `ResumeProfile` |
| `JobMatchAgent` | `agents/job_match_agent.py` | Retrieves candidates via RAG, ranks with LLM |
| `CoverLetterAgent` | `agents/cover_letter_agent.py` | Generates a tailored cover letter |
| `NotificationAgent` | `agents/notification_agent.py` | Sends Pushover push notifications |

<br>

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Groq API (`llama-3.3-70b-versatile`) via OpenAI-compatible client |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector Store** | ChromaDB |
| **UI** | Gradio |
| **Deployment** | Modal (persistent vector store, ASGI web app) |
| **Notifications** | Pushover API |
| **Data Models** | Pydantic |

<br>

## Project Structure

```
job_matcher/
├── agents/
│   ├── agent.py                # Base Agent class (colored logging)
│   ├── resume_agent.py         # Resume parsing
│   ├── job_match_agent.py      # RAG retrieval + LLM ranking
│   ├── cover_letter_agent.py   # Cover letter generation
│   └── notification_agent.py   # Pushover notifications
├── data/
│   ├── models.py                # Pydantic models: Job, ResumeProfile, JobMatch
│   ├── job_loader.py            # JobDataLoader / MockJobLoader
│   └── mock_jobs.py             # 100-job Indian company dataset
├── rag/
│   └── job_rag.py               # ChromaDB vector search
├── app.py                       # Local Gradio UI  (uv run gradio app.py)
├── modal_service.py             # Modal deployment (web UI + API endpoint)
└── config.py                    # Configuration constants & LLM client
```

<br>

## Running Locally

**Prerequisites**

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- A [Groq API key](https://console.groq.com/keys) *(free tier available)*

**Setup**

1. Clone the repository
   ```bash
   git clone https://github.com/aryanrajnitagartala-ai/Multi-Agent_AI_Resume_Copilot.git
   cd Multi-Agent_AI_Resume_Copilot
   ```

2. Create a `.env` file
   ```env
   GROQ_API_KEY=your_groq_key
   PUSHOVER_USER=your_pushover_user      # optional
   PUSHOVER_TOKEN=your_pushover_token    # optional
   ```

3. Run the app
   ```bash
   uv run gradio app.py
   ```

<br>

## Deploying to Modal

1. Install Modal and authenticate
   ```bash
   pip install modal
   modal setup
   ```

2. Create a Groq secret in Modal
   ```bash
   modal secret create groq-secret GROQ_API_KEY=your_groq_key
   ```

3. Test locally before deploying
   ```bash
   uv run modal run modal_service.py
   ```

4. Deploy
   ```bash
   uv run modal deploy modal_service.py
   ```

<br>

## How It Works

1. **Paste your resume** into the text area
2. **Click "Find Matching Jobs"** to kick off the pipeline
3. The app then, step by step:
   - Parses your resume into skills, experience, titles, and a summary
   - Embeds your profile and retrieves candidate jobs from ChromaDB
   - Uses the LLM to re-rank and score the top matches (0.0 – 1.0)
   - Generates a cover letter for your best-scoring match
   - Sends a Pushover notification if the top match scores 80%+
4. **Click any row** in the results table to generate a cover letter for that specific job
5. Watch the **Agent Activity** panel to see every step happen live

<br>

## Configuration

Key settings in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Groq model for parsing, ranking, and generation |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model for semantic search |
| `TOP_K_MATCHES` | `5` | Number of job matches returned |
| `MATCH_SCORE_THRESHOLD` | `0.8` | Minimum score required to trigger a notification |
| `VECTOR_DB_DIR` | `job_vectorstore` | ChromaDB persistence directory |

<br>

## API Access

The Modal deployment also exposes a programmatic function for direct integration:

```python
import modal

search_fn = modal.Function.lookup("job-search-service", "search_and_notify")
result = search_fn.remote(resume_text="Your resume here...")

print(result["profile"])   # Parsed ResumeProfile
print(result["matches"])   # Top matches, each with score, explanation, and cover letter
```

<br>

## Author

**Aryan Raj**
[GitHub @aryanrajnitagartala-ai](https://github.com/aryanrajnitagartala-ai)

<br>

## License

Distributed under the **MIT License**.
