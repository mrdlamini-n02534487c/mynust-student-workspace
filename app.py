import os
import sqlite3
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "mynust.db"

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
app.config.update(
    SECRET_KEY=os.environ.get("MYNUST_SECRET_KEY", "local-development-key-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("MYNUST_COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

CURRENT_MODULES = {
    "SORS2107": "Applied Statistics for Computing",
    "SCS2104": "Structured System Analysis and Design",
    "SCS2114": "Web Development",
}

OPTIONAL_MODULES = {
    "SPH1105": "Electricity and Magnetism",
    "SMA1101": "Calculus",
    "SMA1102": "Linear Algebra",
    "SCS1101": "Introduction to Computer Science and Programming",
    "SCS1103": "Operating Systems",
    "SCS1111": "Principles of Programming Languages",
    "SCS1112": "Fundamentals of Digital Electronics",
    "SCS1211": "Computer Architecture and Organization",
    "SCS1212": "Data Structures and Algorithms",
    "SCS1213": "Database Systems",
    "SCS1214": "Software Engineering",
    "SCS1210": "Discrete Mathematics",
    "SCS1215": "Ethics and Professionalism",
}


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_code TEXT NOT NULL,
                completed_topics TEXT NOT NULL DEFAULT '[]',
                assignments_submitted INTEGER NOT NULL DEFAULT 0,
                quiz_average REAL NOT NULL DEFAULT 0,
                attendance REAL NOT NULL DEFAULT 0,
                exam_mark REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, module_code),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )


def request_data():
    data = request.get_json(silent=True) or {}
    return str(data.get("name", "")).strip(), str(data.get("password", ""))


def validate_credentials(name, password):
    if len(name) < 2 or len(name) > 80:
        return "Name must be between 2 and 80 characters."
    if len(password) < 8 or len(password) > 128:
        return "Password must be between 8 and 128 characters."
    return None


def sign_in(user):
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return jsonify(authenticated=True, name=user["name"])


def authenticated_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_connection() as connection:
        return connection.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.post("/api/register")
def register():
    name, password = request_data()
    validation_error = validate_credentials(name, password)
    if validation_error:
        return jsonify(error=validation_error), 400

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, password_hash) VALUES (?, ?)",
                (name, generate_password_hash(password)),
            )
            user = {"id": cursor.lastrowid, "name": name}
    except sqlite3.IntegrityError:
        return jsonify(error="An account with that name already exists."), 409

    return sign_in(user), 201


@app.post("/api/login")
def login():
    name, password = request_data()
    if not name or not password:
        return jsonify(error="Enter your name and password."), 400

    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, name, password_hash FROM users WHERE name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="The name or password is incorrect."), 401

    return sign_in(user)


@app.get("/api/session")
def current_session():
    if "user_id" not in session:
        return jsonify(authenticated=False), 401
    return jsonify(authenticated=True, name=session["user_name"])


@app.get("/api/modules")
def modules():
    return jsonify(current=CURRENT_MODULES, optional=OPTIONAL_MODULES, academic_level="Level II")


@app.get("/api/study-records")
def study_records():
    user = authenticated_user()
    if user is None:
        return jsonify(error="Authentication required."), 401
    with get_connection() as connection:
        records = connection.execute(
            "SELECT module_code, completed_topics, assignments_submitted, quiz_average, attendance, exam_mark, notes FROM study_records WHERE user_id = ?",
            (user["id"],),
        ).fetchall()
    return jsonify(records=[dict(record) for record in records])


@app.post("/api/study-records")
def save_study_record():
    user = authenticated_user()
    if user is None:
        return jsonify(error="Authentication required."), 401
    data = request.get_json(silent=True) or {}
    module_code = str(data.get("module_code", "")).strip().upper()
    if module_code not in {**CURRENT_MODULES, **OPTIONAL_MODULES}:
        return jsonify(error="Unknown module."), 400
    completed_topics = data.get("completed_topics", [])
    if not isinstance(completed_topics, list):
        return jsonify(error="completed_topics must be a list."), 400
    assignments = max(0, min(10, int(data.get("assignments_submitted", 0))))
    quiz = max(0, min(100, float(data.get("quiz_average", 0))))
    attendance = max(0, min(100, float(data.get("attendance", 0))))
    exam = max(0, min(100, float(data.get("exam_mark", 0))))
    notes = str(data.get("notes", ""))[:5000]
    import json
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO study_records (user_id, module_code, completed_topics, assignments_submitted, quiz_average, attendance, exam_mark, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, module_code) DO UPDATE SET
                completed_topics=excluded.completed_topics,
                assignments_submitted=excluded.assignments_submitted,
                quiz_average=excluded.quiz_average,
                attendance=excluded.attendance,
                exam_mark=excluded.exam_mark,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            """,
            (user["id"], module_code, json.dumps(completed_topics), assignments, quiz, attendance, exam, notes),
        )
    return jsonify(saved=True, module_code=module_code)


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(authenticated=False)


initialize_database()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
