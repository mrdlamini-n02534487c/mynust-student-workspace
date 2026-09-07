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


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(authenticated=False)


initialize_database()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
