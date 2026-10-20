import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

from fastapi import HTTPException, Request


TEACHERS_FILE = Path(__file__).with_name("teachers.json")
SESSION_COOKIE_NAME = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
PASSWORD_ITERATIONS = 310_000
SESSION_SECRET = os.environ.get("TEACHER_SESSION_SECRET") or secrets.token_urlsafe(32)


def load_teachers():
    with TEACHERS_FILE.open(encoding="utf-8") as teachers_file:
        data = json.load(teachers_file)

    teachers = data.get("teachers") if isinstance(data, dict) else None
    if not isinstance(teachers, dict):
        raise ValueError("Teacher credentials must be a JSON object under 'teachers'.")
    return teachers


def hash_password(password):
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return {
        "salt": salt.hex(),
        "password_hash": password_hash.hex(),
    }


def verify_password(password, record):
    try:
        salt = bytes.fromhex(record["salt"])
        expected_hash = bytes.fromhex(record["password_hash"])
    except (KeyError, TypeError, ValueError):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return hmac.compare_digest(actual_hash, expected_hash)


def create_session_token(username, now=None):
    issued_at = int(time.time() if now is None else now)
    payload = json.dumps(
        {"username": username, "expires_at": issued_at + SESSION_DURATION_SECONDS},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def get_session_username(token, now=None):
    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            SESSION_SECRET.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        padding = "=" * (-len(encoded_payload) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(encoded_payload + padding).decode("utf-8")
        )
        current_time = int(time.time() if now is None else now)
        if payload["expires_at"] <= current_time:
            return None
        return payload["username"]
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def get_teacher_username(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    username = get_session_username(token) if token else None
    if not username:
        return None

    if username not in load_teachers():
        return None
    return username


def require_teacher(request: Request):
    username = get_teacher_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Teacher login required.")
    return username