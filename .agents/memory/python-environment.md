---
name: Python environment setup
description: Replit Python base modules may not include pip; package installation requires a Python tools module.
---

Use a Python tools module when a Python project needs third-party packages; the base Python module alone may lack pip and cannot install into the immutable system environment.

**Why:** The initial dependency installation failed because the configured base module had no pip and the system Python was externally managed.

**How to apply:** Check the configured module before installing Python dependencies, and add the appropriate tools module when pip is unavailable.