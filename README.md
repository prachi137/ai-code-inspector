# AI Code Inspector

A FastAPI webhook service that queues an AI review when it receives an opened or synchronized GitHub pull request.

## Run locally

Create a virtual environment, install the project dependencies, and set the credentials the review worker uses:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export GEMINI_API_KEY="your-gemini-api-key"
export GITHUB_TOKEN="your-github-token"
export WEBHOOK_SECRET="your-webhook-secret"

python main.py
```

The server listens on `http://127.0.0.1:8000`.

## Send a sample pull request event

The repository includes a representative payload at [examples/sample_pr_payload.json](examples/sample_pr_payload.json). Send it to the local webhook with:

```bash
curl --request POST http://127.0.0.1:8000/webhook \
  --header "Content-Type: application/json" \
  --header "X-GitHub-Event: pull_request" \
  --data-binary @examples/sample_pr_payload.json
```

The sample uses the deliberately fictitious `example-owner/example-repo` repository. It exercises event parsing and queues the background worker, but that worker cannot fetch the placeholder pull request. To exercise a complete review, replace the repository and pull request fields with a test pull request you can access and configure valid credentials. The worker can post its review as a GitHub comment, so use a disposable test pull request.

The local example omits `X-Hub-Signature-256`; the app verifies the signature when that header is supplied. For signed webhook testing, calculate the signature with your `WEBHOOK_SECRET` and send it with the request.
