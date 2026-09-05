# 🤖 AI Software Employee

> An autonomous AI coding assistant that can understand software tasks, inspect code, modify files, run tests, self-correct failures, and integrate changes with Git and GitHub.

The **AI Software Employee** is an MVP exploring how Large Language Models can perform real software-engineering workflows through controlled tool calling.

Instead of simply generating code in a chat, the AI can actually work inside a controlled workspace.

---

## 🚀 What Can It Do?

The AI Software Employee can:

- 🤖 Understand natural-language software tasks
- 📋 Create a development plan
- 🔍 Inspect project files
- 📖 Read existing source code
- ✏️ Create and modify files
- 🧪 Run Python tests
- 🔧 Analyze test failures
- 🔄 Attempt self-correction
- ✅ Verify successful execution
- 🌿 Create Git branches
- 💾 Create Git commits
- ⬆️ Push branches to GitHub
- 🔀 Create GitHub Pull Requests
- 📊 Display execution activity through a React dashboard

---

## 🧠 How It Works

A typical task follows this workflow:

```text
User
 │
 │  "Add a divide function and tests"
 ▼
React Dashboard
 │
 ▼
FastAPI Backend
 │
 ▼
Autonomous AI Developer
 │
 ├── Understand
 ├── Plan
 ├── Inspect
 ├── Modify
 ├── Test
 ├── Analyze
 ├── Fix
 └── Verify
 │
 ▼
Git / GitHub
 │
 ├── Branch
 ├── Commit
 ├── Push
 └── Pull Request
