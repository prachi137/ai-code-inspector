# 🤖 AI Code Inspector

An automated, serverless code review assistant built with **FastAPI**, **Google Gemini 1.5 Flash**, and **PyGithub**. This service listens to GitHub Webhook events and automatically posts intelligent, constructive code reviews on newly opened or updated Pull Requests (PRs).

---

## ✨ Features

- **Automated PR Reviews**: Triggers instantly whenever a Pull Request is opened or updated (`synchronize` action).
- **Powered by Gemini 1.5 Flash**: Delivers rapid, cost-effective, and insightful AI code reviews highlighting bugs, performance bottlenecks, and security vulnerabilities.
- **Secure Webhook Handling**: Built-in HMAC SHA-256 signature verification to ensure incoming webhooks strictly originate from your GitHub repository.
- **Asynchronous Execution**: Uses FastAPI's `BackgroundTasks` to process reviews in the background, preventing webhook timeouts.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Server**: Uvicorn
- **AI Model**: Google GenAI SDK (`gemini-1.5-flash`)
- **GitHub Integration**: [PyGithub](https://pygithub.readthedocs.io/)
- **Deployment Platform**: Render

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have Python 3.9+ installed along with Git.

### 2. Installation & Setup

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone [https://github.com/prachi137/ai-code-inspector.git](https://github.com/prachi137/ai-code-inspector.git)
cd ai-code-inspector

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
