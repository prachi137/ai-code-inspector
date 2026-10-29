"""Shared test configuration.

Sets dummy credentials before application modules are imported so that
tests never attempt real network calls to GitHub or Gemini.
"""

import os

# Force dummy credentials (must be set before `import main`) so that tests
# never attempt real network calls to GitHub or Gemini.
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["GITHUB_TOKEN"] = "test-github-token"
os.environ["WEBHOOK_SECRET"] = "test-secret"
