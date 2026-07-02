"""
Local Gradio UI for the Job Search LLM App.
Run with: uv run gradio app.py
"""

import io
import logging
import sys
from dotenv import load_dotenv
from ansi2html import Ansi2HTMLConverter

load_dotenv()

import gradio as gr

from agents import ResumeAgent, JobMatchAgent, CoverLetterAgent, NotificationAgent
from data import JobMatch

conv = Ansi2HTMLConverter(inline=True, scheme="dracula")


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

    def get_html(self) -> str:
        """Convert captured ANSI logs to HTML with inline styles."""
        ansi_text = self.log_buffer.getvalue()
        if not ansi_text.strip():
            return '<pre style="background:#282a36; color:#f8f8f2; padding:12px; font-family:monospace; font-size:12px; border-radius:8px; min-height:400px;">Waiting for agent activity...</pre>'
        html = conv.convert(ansi_text, full=False)
        return f'<pre style="background:#282a36; color:#f8f8f2; padding:12px; font-family:monospace; font-size:12px; overflow-x:auto; white-space:pre-wrap; border-radius:8px; min-height:400px; max-height:600px; overflow-y:auto;">{html}</pre>'

    def clear(self):
        """Clear the log buffer."""
        self.log_buffer = io.StringIO()


class JobSearchApp:
    """Job Search Application with Gradio UI."""

    def __init__(self):
        """Initialize all agents and logging."""
        self.log_handler = LogCapture()
        self.log_handler.setFormatter(logging.Formatter('%(message)s'))
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.log_handler)
        
        logging.info("Initializing Job Search App...")
        self.resume_agent = ResumeAgent()
        self.job_match_agent = JobMatchAgent()
        self.cover_letter_agent = CoverLetterAgent()
        self.notification_agent = NotificationAgent()

        self.current_matches: list[JobMatch] = []
        self.current_profile = None
        logging.info("Job Search App ready!")

    def search_jobs(self, resume_text: str):
        """
        Search for matching jobs based on resume.
        Generator that yields updates as each step completes for real-time log streaming.
        
        Yields:
            Tuple of (table_data, profile_summary, cover_letter, status, log_html)
        """
        self.log_handler.clear()

        if not resume_text or len(resume_text.strip()) < 50:
            yield [], "Please paste a resume with at least 50 characters.", "", "", self.log_handler.get_html()
            return

        logging.info("=" * 50)
        logging.info("Finding matching jobs ...")
        yield [], "", "", "Starting job search...", self.log_handler.get_html()

        logging.info("Step 1: Parsing resume...")
        yield [], "", "", "Parsing resume...", self.log_handler.get_html()
        
        self.current_profile = self.resume_agent.parse_resume(resume_text)
        profile_summary = self._format_profile_summary()
        yield [], profile_summary, "", "Resume parsed. Finding matching jobs...", self.log_handler.get_html()

        logging.info("Step 2: Finding matching jobs...")
        yield [], profile_summary, "", "Searching for matching jobs...", self.log_handler.get_html()
        
        self.current_matches = self.job_match_agent.find_matches(self.current_profile)

        if not self.current_matches:
            yield [], "No matching jobs found. Try a different resume.", "", "No matches found.", self.log_handler.get_html()
            return

        table_data = [
            [
                f"⭐ {m.job.title}" if i == 0 else m.job.title,
                m.job.company,
                f"{m.score:.0%}",
                m.job.salary_range or "N/A",
                m.job.location
            ]
            for i, m in enumerate(self.current_matches)
        ]

        yield table_data, profile_summary, "", f"Found {len(self.current_matches)} matches. Generating cover letter...", self.log_handler.get_html()

        best_match = self.current_matches[0]
        logging.info(f"Step 3: Generating cover letter for best match: {best_match.job.title}")
        yield table_data, profile_summary, "", f"Generating cover letter for {best_match.job.title}...", self.log_handler.get_html()
        
        cover_letter = self.cover_letter_agent.generate(self.current_profile, best_match.job)
        yield table_data, profile_summary, cover_letter, "Cover letter generated. Sending notification...", self.log_handler.get_html()

        logging.info(f"Step 4: Sending notification for best match: {best_match.job.title}")
        yield table_data, profile_summary, cover_letter, "Sending notification...", self.log_handler.get_html()
        
        success = self.notification_agent.notify_job_match(
            best_match.job,
            best_match.score,
            cover_letter
        )

        status = (
            f"✅ Notification sent for: {best_match.job.title}"
            if success
            else f"📝 Cover letter generated for: {best_match.job.title}"
        )

        yield table_data, profile_summary, cover_letter, status, self.log_handler.get_html()

    def generate_cover_letter_for_selection(self, evt: gr.SelectData, table_data):
        """
        Generate cover letter for selected job row.
        Generator that yields updates for real-time log streaming.
        
        Yields:
            Tuple of (cover_letter, log_html)
        """
        self.log_handler.clear()

        if not self.current_matches or not self.current_profile:
            yield "Please search for jobs first.", self.log_handler.get_html()
            return

        row_idx = evt.index[0]
        if row_idx >= len(self.current_matches):
            yield "Invalid selection.", self.log_handler.get_html()
            return

        selected_match = self.current_matches[row_idx]
        logging.info(f"Generating cover letter for: {selected_match.job.title}")
        yield "Generating cover letter...", self.log_handler.get_html()

        cover_letter = self.cover_letter_agent.generate(self.current_profile, selected_match.job)
        yield cover_letter, self.log_handler.get_html()

    def _format_profile_summary(self) -> str:
        """Format the profile summary for display."""
        if not self.current_profile:
            return ""

        name = self.current_profile.name or "Unknown"
        skills = ', '.join(self.current_profile.skills[:8]) or "None extracted"
        experience = self.current_profile.years_experience or "?"

        return f"**{name}** | Skills: {skills} | Experience: {experience} years"


def create_ui():
    """Create and return the Gradio UI."""
    app = JobSearchApp()

    css = """
    .job-table tbody tr:first-child {
        background-color: rgba(144, 238, 144, 0.3) !important;
    }
    """

    with gr.Blocks(title="Job Search Assistant", css=css) as ui:
        gr.Markdown("""
# 🔍 Job Search Assistant

Paste your resume below to find matching jobs, generate cover letters, and receive notifications.
        """)

        with gr.Row():
            with gr.Column(scale=2):
                resume_input = gr.Textbox(
                    label="📄 Your Resume",
                    placeholder="Paste your resume here...\n\nExample:\nJohn Smith\nSoftware Engineer with 5 years of experience\nSkills: Python, Django, AWS, Docker, PostgreSQL\nPrevious roles: Backend Developer at TechCo, Software Engineer at StartupXYZ\nEducation: BS Computer Science",
                    lines=8
                )

                search_btn = gr.Button("🔍 Find Matching Jobs", variant="primary", size="lg")

                profile_output = gr.Markdown(label="Extracted Profile")

                jobs_table = gr.Dataframe(
                    headers=["Title", "Company", "Match", "Salary", "Location"],
                    label="📋 Matching Jobs (click row for cover letter)",
                    interactive=False,
                    elem_classes=["job-table"]
                )

                cover_letter_output = gr.Textbox(
                    label="✉️ Generated Cover Letter",
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
            app.search_jobs,
            inputs=[resume_input],
            outputs=[jobs_table, profile_output, cover_letter_output, notification_status, log_output]
        )

        jobs_table.select(
            app.generate_cover_letter_for_selection,
            inputs=[jobs_table],
            outputs=[cover_letter_output, log_output]
        )

        gr.Markdown("""
---
**Tips:**
- Include skills, job titles, and years of experience in your resume
- The app uses RAG to semantically match your profile to job listings
- Cover letters are tailored to each specific job
- Pushover notifications are sent for high-scoring matches (requires PUSHOVER_USER and PUSHOVER_TOKEN env vars)
        """)

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch()
