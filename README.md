# MyNUST web development project

This folder contains the complete MyNUST student workplace for a NUST Zimbabwe Level II Computer Science student.

It also includes `MyNUST_Complete_Project_Documentation.docx`, `MyNUST_Project_Speaker_Notes.docx`, `MyNUST_Lecture_Notes.docx`, and `MyNUST_Project_Proposal.docx`. These documents cover the three current modules, all 16 academic foundations, algorithms, data structures, backend/API design, security, testing and limitations.

The project scope is your current academic level. The default student view focuses on SORS2107, SCS2104 and SCS2114, because these are the modules currently being studied. Earlier modules supply supporting knowledge: programming, operating systems, programming languages, databases, software engineering, discrete mathematics, ethics, algorithms and the mathematical foundations. The remaining 13 modules can be added from the module picker without changing another student's library.

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

The first user can create an account from the sign-in screen. Passwords are hashed with Werkzeug and are never stored as plain text. Sessions are stored in an HTTP-only cookie. Account records and per-user study records are stored in `mynust.db`, which is created on first run.

Backend API routes include `/api/register`, `/api/login`, `/api/session`, `/api/logout`, `/api/modules`, `/api/study-records` (GET) and `/api/study-records` (POST).

For production deployment, set a strong `MYNUST_SECRET_KEY`, enable HTTPS, set `MYNUST_COOKIE_SECURE=1`, and use a managed database with backups. GitHub Pages can host the static frontend but cannot run this Flask backend, so the authenticated version must be deployed to a Python-capable host such as Render, Railway, or a VPS.
