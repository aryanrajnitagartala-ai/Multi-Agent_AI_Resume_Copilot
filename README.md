🔍 Job Matcher
Live App: https://aryanrajnitagartala-ai--job-search-service-web-ui.modal.run/
An AI-powered job search assistant that parses your resume, matches it to relevant job listings using semantic search (RAG), generates tailored cover letters, and sends notifications for high-scoring matches — all through a multi-agent pipeline you can watch work in real time.
![Job Matcher Demo](https://raw.githubusercontent.com/aryanrajnitagartala-ai/Multi-Agent_AI_Resume_Copilot/main/Screenshot%202026-07-02%20125537.png)
> Paste your resume → Find matching jobs → Generate cover letters → Get notifications
Features
Resume Parsing — Extracts name, email, skills, years of experience, job titles, education, and a background summary from raw resume text
Semantic Job Matching — Uses RAG (ChromaDB + sentence-transformers) to retrieve candidate jobs, then an LLM re-ranks and scores them against your profile
Cover Letter Generation — Generates a tailored, ready-to-send cover letter for any matched job
Push Notifications — Sends a Pushover notification automatically when a match scores 80%+ (falls back to a dry-run log if credentials aren't set)
Live Agent Activity Log — A real-time, color-coded log panel shows each agent's steps as the pipeline runs
Curated Dataset — 100 Indian company job listings with ₹ LPA salary ranges
Architecture
A multi-agent pipeline, each agent with a single responsibility:
```
Resume Text
     │
     ▼
┌────────────────────┐
│   Resume Agent      │  Parses resume → structured ResumeProfile
└──────────┬──────────┘
           ▼
┌────────────────────┐
│  Job Match Agent     │  RAG search (ChromaDB) → LLM re-ranks top N matches
└──────────┬──────────┘
           ▼
┌────────────────────┐
│ Cover Letter Agent   │  Generates a tailored cover letter for the best match
└──────────┬──────────┘
           ▼
┌────────────────────┐
│ Notification Agent   │  Sends a Pushover alert for 80%+ matches (or dry-run)
└────────────────────┘
```
Agent	File	Purpose
`ResumeAgent`	`agents/resume_agent.py`	Parses resume text into a structured `ResumeProfile`
`JobMatchAgent`	`agents/job_match_agent.py`	Retrieves candidates via RAG, ranks with LLM
`CoverLetterAgent`	`agents/cover_letter_agent.py`	Generates a tailored cover letter
`NotificationAgent`	`agents/notification_agent.py`	Sends Pushover push notifications
Tech Stack
Layer	Technology
LLM	Groq API (`llama-3.3-70b-versatile`) via OpenAI-compatible client
Embeddings	`sentence-transformers/all-MiniLM-L6-v2`
Vector Store	ChromaDB
UI	Gradio
Deployment	Modal (persistent vector store, ASGI web app)
Notifications	Pushover API
Data Models	Pydantic
Project Structure
```
job_matcher/
├── agents/
│   ├── agent.py               # Base Agent class (colored logging)
│   ├── resume_agent.py        # Resume parsing
│   ├── job_match_agent.py     # RAG retrieval + LLM ranking
│   ├── cover_letter_agent.py  # Cover letter generation
│   └── notification_agent.py  # Pushover notifications
├── data/
│   ├── models.py               # Pydantic models: Job, ResumeProfile, JobMatch
│   ├── job_loader.py           # JobDataLoader / MockJobLoader
│   └── mock_jobs.py            # 100-job Indian company dataset
├── rag/
│   └── job_rag.py              # ChromaDB vector search
├── app.py                      # Local Gradio UI (uv run gradio app.py)
├── modal_service.py            # Modal deployment (web UI + API endpoint)
└── config.py                   # Configuration constants & LLM client
```
Running Locally
Prerequisites
Python 3.11+
uv package manager
A Groq API key (free tier available)
Setup
Clone the repository:
```bash
   git clone https://github.com/aryanrajnitagartala-ai/Multi-Agent_AI_Resume_Copilot.git
   cd Multi-Agent_AI_Resume_Copilot
   ```
Create a `.env` file:
```
   GROQ_API_KEY=your_groq_key
   PUSHOVER_USER=your_pushover_user    # Optional
   PUSHOVER_TOKEN=your_pushover_token  # Optional
   ```
Run the app:
```bash
   uv run gradio app.py
   ```
Deploying to Modal
Install Modal and authenticate:
```bash
   pip install modal
   modal setup
   ```
Create a Groq secret in Modal:
```bash
   modal secret create groq-secret GROQ_API_KEY=your_groq_key
   ```
Test locally before deploying:
```bash
   uv run modal run modal_service.py
   ```
Deploy:
```bash
   uv run modal deploy modal_service.py
   ```
How It Works
Paste your resume into the text area
Click "Find Matching Jobs" to kick off the pipeline
The app, step by step:
Parses your resume into skills, experience, titles, and a summary
Embeds your profile and retrieves candidate jobs from ChromaDB
Uses the LLM to re-rank and score the top matches (0.0–1.0)
Generates a cover letter for your best-scoring match
Sends a Pushover notification if the top match scores 80%+
Click any row in the results table to generate a cover letter for that specific job
Watch the Agent Activity panel to see each step happen live
Configuration
Key settings in `config.py`:
Setting	Default	Description
`LLM_MODEL`	`llama-3.3-70b-versatile`	Groq model for parsing, ranking, and generation
`EMBEDDING_MODEL`	`all-MiniLM-L6-v2`	Sentence-transformers model for semantic search
`TOP_K_MATCHES`	5	Number of job matches returned
`MATCH_SCORE_THRESHOLD`	0.8	Minimum score required to trigger a notification
`VECTOR_DB_DIR`	`job_vectorstore`	ChromaDB persistence directory
API Access
The Modal deployment also exposes a programmatic function for direct integration:
```python
import modal

search_fn = modal.Function.lookup("job-search-service", "search_and_notify")
result = search_fn.remote(resume_text="Your resume here...")

print(result["profile"])   # Parsed ResumeProfile
print(result["matches"])   # Top matches, each with score, explanation, and cover letter
```
Author
Aryan Raj — aryanrajnitagartala-ai
License
MIT


