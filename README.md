# Job Matcher

**Live App:** https://davenjeru--job-search-service-web-ui.modal.run

An AI-powered job search assistant that matches your resume to relevant job listings using semantic search and generates tailored cover letters.

## Features

- **Resume Parsing** - Extracts skills, experience, and job titles from your resume using GPT-4o-mini
- **Semantic Job Matching** - Uses RAG (Retrieval-Augmented Generation) with ChromaDB and sentence-transformers to find jobs that match your profile
- **Cover Letter Generation** - Automatically generates personalized cover letters tailored to each job
- **Push Notifications** - Sends Pushover notifications for high-scoring matches (80%+)
- **Real-time Agent Activity** - Watch the AI agents work in real-time through the activity log

## Architecture

The application uses a multi-agent architecture:

| Agent | Purpose |
|-------|---------|
| **ResumeAgent** | Parses resume text into a structured profile |
| **JobMatchAgent** | Finds matching jobs using vector similarity search |
| **CoverLetterAgent** | Generates tailored cover letters |
| **NotificationAgent** | Sends push notifications for top matches |

### Tech Stack

- **Frontend**: Gradio
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Store**: ChromaDB
- **Deployment**: Modal
- **Notifications**: Pushover API

## Project Structure

```
job_matcher/
├── agents/
│   ├── agent.py              # Base agent class
│   ├── resume_agent.py       # Resume parsing
│   ├── job_match_agent.py    # Job matching
│   ├── cover_letter_agent.py # Cover letter generation
│   └── notification_agent.py # Push notifications
├── data/
│   ├── models.py             # Pydantic models (Job, ResumeProfile, JobMatch)
│   ├── job_loader.py         # Job data loading
│   └── mock_jobs.py          # Sample job listings
├── rag/
│   └── job_rag.py            # ChromaDB vector search
├── app.py                    # Local Gradio UI
├── modal_service.py          # Modal deployment
└── config.py                 # Configuration constants
```

## Running Locally

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key

### Setup

1. Clone the repository and navigate to the project directory

2. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   PUSHOVER_USER=your_pushover_user    # Optional
   PUSHOVER_TOKEN=your_pushover_token  # Optional
   ```

3. Install dependencies and run:
   ```bash
   uv run gradio app.py
   ```

## Deploying to Modal

1. Install Modal and authenticate:
   ```bash
   pip install modal
   modal setup
   ```

2. Create an OpenAI secret in Modal:
   ```bash
   modal secret create openai-secret OPENAI_API_KEY=your_key
   ```

3. Deploy:
   ```bash
   uv run modal deploy modal_service.py
   ```

4. Test locally before deploying:
   ```bash
   uv run modal run modal_service.py
   ```

## How It Works

1. **Paste your resume** into the text area
2. **Click "Find Matching Jobs"** to start the pipeline
3. The app:
   - Parses your resume to extract skills and experience
   - Searches the job database using semantic similarity
   - Returns the top 5 matching jobs ranked by score
   - Generates a cover letter for the best match
   - Sends a notification if the match score is 80%+
4. **Click any job row** to generate a cover letter for that specific position

## Configuration

Key settings in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_MODEL` | gpt-4o-mini | OpenAI model for text generation |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Model for semantic embeddings |
| `TOP_K_MATCHES` | 5 | Number of job matches to return |
| `MATCH_SCORE_THRESHOLD` | 0.8 | Minimum score for notifications |

## API Access

The Modal deployment also exposes a programmatic endpoint:

```python
import modal

search_fn = modal.Function.lookup("job-search-service", "search_and_notify")
result = search_fn.remote(resume_text="Your resume here...")

print(result["profile"])   # Parsed profile
print(result["matches"])   # Top 5 matches with cover letters
```

## License

MIT
