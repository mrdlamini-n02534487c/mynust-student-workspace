# MyNUST web development project

This folder contains the complete MyNUST student workplace with real server-side authentication.

It also includes `MyNUST_Project_Speaker_Notes.docx`, a word-for-word presentation script for demonstrating the project.

## Progress calculation

Module progress is calculated per student using: completed topics (25%), submitted assignments (20%), quiz average (20%), attendance (15%), and exam mark (20%). The module panel shows the evidence fields and recalculates the result immediately.

## Run locally

PowerShell:

```powershell
cd "web development"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:MYNUST_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python app.py
```

Open http://127.0.0.1:5000/.

The first user can create an account from the sign-in screen. Passwords are hashed with Werkzeug and are never stored as plain text. Sessions are stored in an HTTP-only cookie and the account records are stored in `mynust.db`, which is created on first run.

For production deployment, set a strong `MYNUST_SECRET_KEY`, enable HTTPS, set `MYNUST_COOKIE_SECURE=1`, and use a managed database with backups. GitHub Pages can host the static frontend but cannot run this Flask backend, so the authenticated version must be deployed to a Python-capable host such as Render, Railway, or a VPS.
