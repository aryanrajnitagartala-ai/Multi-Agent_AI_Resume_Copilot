"""
Modal deployment service for the Job Search LLM App.

Deploy with: uv run modal deploy modal_service.py
Local test: uv run modal run modal_service.py
"""

import io
import logging
from pathlib import Path

import modal
import gradio as gr
from fastapi import FastAPI
from gradio.routes import mount_gradio_app

app = modal.App("job-search-service")

local_dir = Path(__file__).parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "openai",
        "chromadb",
        "sentence-transformers",
        "pydantic",
        "requests",
        "python-dotenv",
        "gradio",
        "ansi2html"
    )
    .add_local_dir(local_dir, remote_path="/root")
)

secrets = [
    modal.Secret.from_name("groq-secret"),
]


class LogCapture(logging.Handler):
    """Custom logging handler that captures logs with ANSI codes for HTML display."""

    def __init__(self):
        super().__init__()
        self.log_buffer = io.StringIO()

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_buffer.write(msg + "\n")
        except Exception:
            pass

    def get_html(self, conv) -> str:
        """Convert captured ANSI logs to HTML with inline styles."""
        ansi_text = self.log_buffer.getvalue()
        if not ansi_text.strip():
            return '<pre style="background:#282a36; color:#f8f8f2; padding:12px; font-family:monospace; font-size:12px; border-radius:8px; min-height:400px;">Waiting for agent activity...</pre>'
        html = conv.convert(ansi_text, full=False)
        return f'<pre style="background:#282a36; color:#f8f8f2; padding:12px; font-family:monospace; font-size:12px; overflow-x:auto; white-space:pre-wrap; border-radius:8px; min-height:400px; max-height:600px; overflow-y:auto;">{html}</pre>'

    def clear(self):
        """Clear the log buffer."""
        self.log_buffer = io.StringIO()


@app.function(image=image, secrets=secrets, timeout=600)
@modal.concurrent(max_inputs=10)
@modal.asgi_app()
def web_ui():
    """Serve the Gradio UI as a web endpoint."""
    import sys
    sys.path.insert(0, "/root")

    from ansi2html import Ansi2HTMLConverter
    from agents import ResumeAgent, JobMatchAgent, CoverLetterAgent, NotificationAgent
    from data import JobMatch

    conv = Ansi2HTMLConverter(inline=True, scheme="dracula")
    
    log_handler = LogCapture()
    log_handler.setFormatter(logging.Formatter('%(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(log_handler)

    logging.info("Initializing Job Search App...")
    resume_agent = ResumeAgent()
    job_match_agent = JobMatchAgent()
    cover_letter_agent = CoverLetterAgent()
    notification_agent = NotificationAgent()
    logging.info("Job Search App ready!")

    current_matches = []
    current_profile = None

    def search_jobs(resume_text: str):
        """Generator that yields updates as each step completes for real-time log streaming."""
        nonlocal current_matches, current_profile
        log_handler.clear()

        if not resume_text or len(resume_text.strip()) < 50:
            yield [], "Please paste a resume (50+ chars).", "", "", log_handler.get_html(conv)
            return

        logging.info("=" * 50)
        logging.info("Finding matching jobs ...")
        yield [], "", "", "Starting job search...", log_handler.get_html(conv)

        logging.info("Step 1: Parsing resume...")
        yield [], "", "", "Parsing resume...", log_handler.get_html(conv)
        
        current_profile = resume_agent.parse_resume(resume_text)
        profile_summary = _format_profile(current_profile)
        yield [], profile_summary, "", "Resume parsed. Finding matching jobs...", log_handler.get_html(conv)

        logging.info("Step 2: Finding matching jobs...")
        yield [], profile_summary, "", "Searching for matching jobs...", log_handler.get_html(conv)
        
        current_matches = job_match_agent.find_matches(current_profile)

        if not current_matches:
            yield [], "No matches found.", "", "No matches found.", log_handler.get_html(conv)
            return

        table_data = [
            [
                f"⭐ {m.job.title}" if i == 0 else m.job.title,
                m.job.company,
                f"{m.score:.0%}",
                m.job.salary_range or "N/A",
                m.job.location
            ]
            for i, m in enumerate(current_matches)
        ]

        yield table_data, profile_summary, "", f"Found {len(current_matches)} matches. Generating cover letter...", log_handler.get_html(conv)

        best = current_matches[0]
        logging.info(f"Step 3: Generating cover letter for best match: {best.job.title}")
        yield table_data, profile_summary, "", f"Generating cover letter for {best.job.title}...", log_handler.get_html(conv)
        
        cover_letter = cover_letter_agent.generate(current_profile, best.job)
        yield table_data, profile_summary, cover_letter, "Cover letter generated. Sending notification...", log_handler.get_html(conv)

        logging.info(f"Step 4: Sending notification for best match: {best.job.title}")
        yield table_data, profile_summary, cover_letter, "Sending notification...", log_handler.get_html(conv)
        
        success = notification_agent.notify_job_match(best.job, best.score, cover_letter)

        status = (
            f"✅ Notified: {best.job.title}"
            if success
            else f"📝 Generated for {best.job.title}"
        )

        yield table_data, profile_summary, cover_letter, status, log_handler.get_html(conv)

    def _format_profile(profile) -> str:
        if not profile:
            return ""
        name = profile.name or "Unknown"
        skills = ', '.join(profile.skills[:8]) or "None"
        exp = profile.years_experience or "?"
        return f"**{name}** | Skills: {skills} | {exp} years"

    def generate_cover_letter(evt: gr.SelectData, table_data):
        """Generator that yields updates for real-time log streaming."""
        nonlocal current_matches, current_profile
        log_handler.clear()

        if not current_matches or not current_profile:
            yield "Search first.", log_handler.get_html(conv)
            return

        if evt.index[0] >= len(current_matches):
            yield "Invalid selection.", log_handler.get_html(conv)
            return

        selected = current_matches[evt.index[0]]
        logging.info(f"Generating cover letter for: {selected.job.title}")
        yield "Generating cover letter...", log_handler.get_html(conv)
        
        cover_letter = cover_letter_agent.generate(current_profile, selected.job)
        yield cover_letter, log_handler.get_html(conv)

    css = ".job-table tbody tr:first-child { background-color: rgba(144, 238, 144, 0.3) !important; }"

    with gr.Blocks(title="Job Search Assistant", css=css) as ui:
        gr.Markdown("""
# 🔍 Job Search Assistant

Paste your resume → Find matching jobs → Generate cover letters → Get notifications
        """)

        with gr.Row():
            with gr.Column(scale=2):
                resume_input = gr.Textbox(
                    label="📄 Resume",
                    lines=8,
                    placeholder="Paste your resume here..."
                )

                search_btn = gr.Button("🔍 Find Matching Jobs", variant="primary", size="lg")

                profile_output = gr.Markdown()

                jobs_table = gr.Dataframe(
                    headers=["Title", "Company", "Match", "Salary", "Location"],
                    interactive=False,
                    elem_classes=["job-table"]
                )

                cover_letter_output = gr.Textbox(
                    label="✉️ Cover Letter",
                    lines=12,
                    interactive=False
                )

                notification_status = gr.Textbox(
                    label="📬 Status",
                    interactive=False
                )

            with gr.Column(scale=1):
                gr.Markdown("### 🤖 Agent Activity")
                log_output = gr.HTML(
                    value='<pre style="background:#282a36; color:#f8f8f2; padding:12px; font-family:monospace; font-size:12px; border-radius:8px; min-height:400px;">Waiting for agent activity...</pre>'
                )

        search_btn.click(
            search_jobs,
            inputs=[resume_input],
            outputs=[jobs_table, profile_output, cover_letter_output, notification_status, log_output]
        )

        jobs_table.select(
            generate_cover_letter,
            inputs=[jobs_table],
            outputs=[cover_letter_output, log_output]
        )

    return mount_gradio_app(app=FastAPI(), blocks=ui, path="/")


@app.function(image=image, secrets=secrets, timeout=300)
def search_and_notify(resume_text: str) -> dict:
    """
    Full pipeline function for programmatic access.
    
    Args:
        resume_text: Raw resume text.
        
    Returns:
        Dict with profile and matches.
    """
    import sys
    sys.path.insert(0, "/root")

    from agents import ResumeAgent, JobMatchAgent, CoverLetterAgent, NotificationAgent

    resume_agent = ResumeAgent()
    job_match_agent = JobMatchAgent()
    cover_letter_agent = CoverLetterAgent()
    notification_agent = NotificationAgent()

    profile = resume_agent.parse_resume(resume_text)
    matches = job_match_agent.find_matches(profile)

    results = []
    for match in matches[:5]:
        cover_letter = cover_letter_agent.generate(profile, match.job)
        results.append({
            "job": match.job.model_dump(),
            "score": match.score,
            "explanation": match.explanation,
            "cover_letter": cover_letter
        })

        if match.score >= 0.8:
            notification_agent.notify_job_match(match.job, match.score, cover_letter)

    return {
        "profile": profile.model_dump(),
        "matches": results
    }


@app.local_entrypoint()
def main():
    """Local test entrypoint."""
    test_resume = """
    John Smith
    Senior Python Developer
    
    Skills: Python, Django, FastAPI, AWS, Docker, PostgreSQL, REST APIs, Microservices
    
    Experience: 5 years of backend development
    
    Previous roles:
    - Backend Developer at TechCorp (3 years)
    - Software Engineer at StartupXYZ (2 years)
    
    Education: BS Computer Science, Stanford University
    
    Built scalable microservices handling millions of requests. Led team of 3 developers.
    Strong experience with cloud infrastructure and CI/CD pipelines.
    """

    print("Testing resume parsing and job matching...")
    result = search_and_notify.remote(test_resume)
    print(f"Found {len(result['matches'])} matches")

    if result['matches']:
        best = result['matches'][0]
        print(f"\nBest match: {best['job']['title']} at {best['job']['company']}")
        print(f"Score: {best['score']:.0%}")
        print(f"\nCover letter preview:\n{best['cover_letter'][:300]}...")
