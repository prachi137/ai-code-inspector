import re
import os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from config import settings
from utils.security import verify_github_signature
from services.ai_service import inspect_code_diff
from services.github_service import fetch_pr_diff, post_github_comment
from github import Github
from google import genai

app = FastAPI(
    title="AI Code Inspector API",
    description="Automated AI PR Code Reviewer built with FastAPI and Gemini 1.5 Flash",
    version="1.0.0"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

genai_client = genai.Client(api_key=GEMINI_API_KEY)
github_client = Github(GITHUB_TOKEN)

LOCK_FILE_PATTERNS = [
    r'package-lock\.json$',
    r'poetry\.lock$',
    r'yarn\.lock$',
    r'Pipfile\.lock$',
    r'composer\.lock$',
    r'Gemfile\.lock$',
    r'cargo\.lock$',
    r'go\.sum$',
    r'requirements\.txt$',  # often large generated updates
]

def is_lock_or_generated_file(filename: str) -> bool:
    """Return True if the file should be excluded from AI review (lock/generated)."""
    for pattern in LOCK_FILE_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False

def process_pull_request_event(repo_full_name: str, pr_number: int, diff_url: str):
    """
    Background worker function that fetches PR diff, runs Gemini AI inspection,
    and posts the result as a comment on GitHub.
    """
    # 1. Fetch raw diff from GitHub
    diff_text = fetch_pr_diff(diff_url)
    if not diff_text.strip():
        print(f"Skipping PR #{pr_number}: Empty or inaccessible diff.")
        return

    # 2. Perform AI Inspection via Gemini 1.5 Flash
    review_result = inspect_code_diff(diff_text)

    # 3. Post review feedback as a PR comment
    post_github_comment(repo_full_name, pr_number, review_result)

def run_ai_code_review(repo_full_name: str, pr_number: int):
    try:
        repo = github_client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)

        files = pr.get_files()
        diff_text = ""
        skipped_files = []
        for file in files:
            if is_lock_or_generated_file(file.filename):
                skipped_files.append(file.filename)
                continue
            if file.patch:
                diff_text += f"\nFile: {file.filename}\nChanges:\n{file.patch}\n"

        if skipped_files:
            print(f"Skipped lock/generated files from AI review: {', '.join(skipped_files)}")

        if not diff_text:
            print("No code changes found to review.")
            return

        prompt = f"""
        You are an expert AI code reviewer. Review the following pull request code diff. 
        Identify any bugs, security issues, performance bottlenecks, or style improvements.
        Keep the review concise, constructive, and formatted in Markdown.

        Code Diff:
        {diff_text}
        """

        response = genai_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        review_comment = f"### 🤖 Gemini AI Code Inspector Review\n\n{response.text}"

        pr.create_issue_comment(review_comment)
        print(f"Successfully posted AI review on PR #{pr_number}")

    except Exception as e:
        print(f"Error in AI code review execution: {str(e)}")

@app.post("/webhook")
async def handle_github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None)
):
    try:
        body = await request.body()
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        # 1. Sabse pehle 'ping' check kar lo taaki test ping bina kisi error ke pass ho jaye
        if event_type == "ping":
            return {"status": "success", "message": "Pong! Webhook is active."}

        # 2. Signature verification (agar secret set hai)
        if x_hub_signature_256:
            verify_github_signature(body, x_hub_signature_256)

        payload = await request.json()

        # 3. Pull Request events handle karo
        if event_type == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
            pr_number = payload["pull_request"]["number"]
            repo_full_name = payload["repository"]["full_name"]
            background_tasks.add_task(run_ai_code_review, repo_full_name, pr_number)

        return {"status": "success", "message": f"Event {event_type} received successfully"}

    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    """
    Health check endpoint for cloud hosting monitoring (Render/UptimeRobot).
    """
    return {"status": "healthy", "service": "AI Code Inspector"}

@app.get("/")
def read_root():
    return {
        "status": "active",
        "message": "AI GitHub PR Code Inspector Bot is live and running successfully!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
