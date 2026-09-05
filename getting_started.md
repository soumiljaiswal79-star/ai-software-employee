# Getting Started

This guide explains how to set up and run the AI Software Employee locally.

## Create Python Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

### Windows

```powershell
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

---

## Install Backend Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

The AI Software Employee requires credentials for Gemini and GitHub.

Set the following environment variables:

```text
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token
```

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
$env:GITHUB_TOKEN="your_github_token"
```

### macOS / Linux

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export GITHUB_TOKEN="your_github_token"
```

> **Security:** Never commit API keys, tokens, passwords, or other secrets to GitHub.

---

## Start the Backend

From the project root directory, run:

```bash
python -m uvicorn app.main:app --reload
```

The FastAPI backend will run at:

```text
http://127.0.0.1:8000
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Start the Frontend

Open a **second terminal** and navigate to the frontend directory:

```bash
cd frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The dashboard will be available at:

```text
http://localhost:5173
```

Open this address in your browser.

---

## Run Tests

From the project root directory, run:

```bash
python -m pytest tests workspace
```

The test suite should complete successfully.

---

## Try Your First Task

Open the dashboard at:

```text
http://localhost:5173
```

Enter a software task such as:

```text
Create a file called workspace/demo.py containing a function hello() that returns "Hello from AI Software Employee", and create a test that verifies it.
```

Click **Run Task**.

The AI Software Employee will:

```text
Understand
    ↓
Inspect
    ↓
Modify
    ↓
Test
    ↓
Fix if necessary
    ↓
Verify
    ↓
Report
```

---

## GitHub Integration

The AI Software Employee supports Git and GitHub operations.

Supported operations include:

- Git repository initialization
- Git status
- Git diff
- Branch creation
- Git commit
- Git push
- GitHub authentication
- GitHub repository access
- GitHub branch creation
- Pull Request creation

GitHub credentials must be configured before using GitHub-related features.

---

## Development Workflow

For local development, use two terminals.

### Terminal 1 — Backend

From the project root:

```bash
python -m uvicorn app.main:app --reload
```

### Terminal 2 — Frontend

From the frontend directory:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://localhost:5173
```

### Autonomous Development Workflow

The AI Software Employee follows this workflow:

```text
User Task
    ↓
Understand
    ↓
Plan
    ↓
Inspect Files
    ↓
Modify Code
    ↓
Run Tests
    ↓
Analyze Results
    ↓
Fix Failures
    ↓
Retest
    ↓
Verify
    ↓
Report
```

The autonomous loop is intentionally bounded to prevent uncontrolled execution and excessive LLM usage.

---

## Troubleshooting

### Gemini API Error

Make sure `GEMINI_API_KEY` is configured correctly and available in the environment where the backend is running.

### GitHub Authentication Error

Make sure `GITHUB_TOKEN` is configured correctly and has the required repository permissions.

### Frontend Cannot Connect to Backend

Make sure the FastAPI backend is running at:

```text
http://127.0.0.1:8000
```

Then restart the Vite development server:

```bash
npm run dev
```

### Tests Are Not Running

Make sure you are running the test command from the project root:

```bash
python -m pytest tests workspace
```

### Virtual Environment Is Not Activated

#### Windows

```powershell
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
source .venv/bin/activate
```
