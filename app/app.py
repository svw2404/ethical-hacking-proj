import os
import re
import sqlite3
import hashlib
import base64
import logging
import time
from collections import defaultdict
from flask import (
    Flask, render_template, request, session, redirect, url_for, g
)

app = Flask(__name__)
# Intentionally weak secret key — for demonstration only.
# Production apps must use a long random secret from environment variables.
app.secret_key = "atlas-core-dev-key-changeme"

BASE_DIR = os.path.dirname(__file__)
DB_PATH  = os.path.join(BASE_DIR, "database.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "access.log")

# ── Mission 2 payload (generated at startup, always correct) ──────────────────

def _caesar(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)

_FLAG2          = "picoCTF{layered_encoding_is_not_crypto}"
_shifted        = _caesar(_FLAG2, 3)          # Caesar +3
_reversed       = _shifted[::-1]              # reverse
MISSION2_PAYLOAD = base64.b64encode(_reversed.encode()).decode()  # Base64

# ── Logging ───────────────────────────────────────────────────────────────────

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

_file_handler = logging.FileHandler(LOG_PATH)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger = logging.getLogger("ctf")
logger.setLevel(logging.INFO)
logger.addHandler(_file_handler)

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()

def get_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

# ── Rate limiter (in-memory, for secure-login demo) ───────────────────────────

_attempts: dict[str, list[float]] = defaultdict(list)
_WINDOW   = 60   # seconds
_MAX      = 5    # max attempts per window

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < _WINDOW]
    if len(_attempts[ip]) >= _MAX:
        return True
    _attempts[ip].append(now)
    return False

# ── SQLi pattern detector (for logging only — not a WAF) ─────────────────────

_SQLI_RE = re.compile(
    r"('|--|;|OR\s+\d+=\d+|UNION|SELECT|DROP|INSERT|UPDATE|DELETE|1=1)",
    re.IGNORECASE,
)

def looks_like_sqli(text: str) -> bool:
    return bool(_SQLI_RE.search(text))

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Mission 1 — Easy ──────────────────────────────────────────────────────────

@app.route("/mission1")
def mission1():
    return render_template("mission1.html")


# ── Mission 2 — Medium ────────────────────────────────────────────────────────

@app.route("/mission2")
def mission2():
    return render_template("mission2.html", payload=MISSION2_PAYLOAD)


# ── Mission 3 — Hard — VULNERABLE login ──────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    debug_query = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        ip = get_ip()

        logger.info(f"[INFO]    Login attempt  username={username}  ip={ip}")

        if looks_like_sqli(username) or looks_like_sqli(password):
            logger.warning(
                f"[WARNING] SQL injection payload detected  ip={ip}"
                f"  payload_user={username!r}  payload_pass={password!r}"
            )

        # ── INTENTIONALLY VULNERABLE ──────────────────────────────────────────
        # String concatenation builds the query directly from user input.
        # Payload  ' OR '1'='1' --  bypasses this check completely.
        # This is here to demonstrate OWASP A03 Injection for the CTF lab.
        # NEVER do this in production code.
        # ─────────────────────────────────────────────────────────────────────
        query = (
            f"SELECT * FROM users WHERE username='{username}'"
            f" AND password='{password}'"
        )
        debug_query = query  # shown in error message (intentional info disclosure)

        db = get_db()
        try:
            user = db.execute(query).fetchone()
        except Exception as exc:
            logger.error(f"[ERROR]   DB error  ip={ip}  error={exc}")
            error = f"Database error: {exc}"
            return render_template("login.html", error=error, debug_query=debug_query)

        if user:
            session.clear()
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["role"]     = user["role"]
            logger.info(f"[INFO]    Login success  username={user['username']}  ip={ip}")
            return redirect(url_for("profile", id=user["id"]))

        logger.warning(f"[WARNING] Login failed  username={username}  ip={ip}")
        error = f"Invalid credentials. Executed query: {debug_query}"

    return render_template("login.html", error=error, debug_query=debug_query)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Mission 3 — Hard — VULNERABLE profile (IDOR) ─────────────────────────────

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    profile_id = request.args.get("id", str(session["user_id"]))
    ip = get_ip()

    if profile_id != str(session["user_id"]):
        logger.warning(
            f"[WARNING] Profile IDOR  session_user={session['user_id']}"
            f"  requested_profile={profile_id}  ip={ip}"
        )

    # ── INTENTIONALLY VULNERABLE ──────────────────────────────────────────────
    # The backend trusts the ?id= parameter and returns any profile without
    # checking whether the logged-in user is authorized to view it.
    # Changing ?id=102 to ?id=1 reveals the administrator profile + flag.
    # ─────────────────────────────────────────────────────────────────────────
    db = get_db()
    prof = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()

    return render_template(
        "profile.html",
        profile=prof,
        session_user=session["username"],
        session_role=session["role"],
        own=(profile_id == str(session["user_id"])),
    )


# ── Mission 3 — SECURE login (comparison) ────────────────────────────────────

@app.route("/secure-login", methods=["GET", "POST"])
def secure_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ip = get_ip()

        logger.info(f"[INFO]    Secure login attempt  username={username}  ip={ip}")

        # Rate limiting
        if is_rate_limited(ip):
            logger.warning(f"[WARNING] Rate limit exceeded  ip={ip}")
            error = "Too many login attempts. Please wait 60 seconds."
            return render_template("secure_login.html", error=error)

        if looks_like_sqli(username) or looks_like_sqli(password):
            logger.warning(
                f"[WARNING] SQLi attempt BLOCKED at secure-login  ip={ip}"
                f"  payload={username!r}"
            )

        # ── SECURE: parameterized query + hashed password comparison ──────────
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and user["password_hash"] == sha256(password):
            session.clear()
            session["user_id"]     = user["id"]
            session["username"]    = user["username"]
            session["role"]        = user["role"]
            session["secure_mode"] = True
            logger.info(f"[INFO]    Secure login success  username={username}  ip={ip}")
            return redirect(url_for("secure_profile", id=user["id"]))

        # Generic error — no info about which field was wrong
        logger.warning(f"[WARNING] Secure login failed  username={username}  ip={ip}")
        error = "Invalid credentials."

    return render_template("secure_login.html", error=error)


@app.route("/secure-logout")
def secure_logout():
    session.clear()
    return redirect(url_for("secure_login"))


# ── Mission 3 — SECURE profile (authorization check) ─────────────────────────

@app.route("/secure-profile")
def secure_profile():
    if "user_id" not in session or not session.get("secure_mode"):
        return redirect(url_for("secure_login"))

    requested_id = request.args.get("id", str(session["user_id"]))
    ip = get_ip()

    # ── SECURE: server-side authorization check ───────────────────────────────
    if requested_id != str(session["user_id"]) and session.get("role") != "admin":
        logger.warning(
            f"[WARNING] Secure profile: BLOCKED unauthorized access"
            f"  session_user={session['user_id']}  requested={requested_id}  ip={ip}"
        )
        return render_template(
            "secure_profile.html",
            profile=None,
            blocked=True,
            session_user=session["username"],
        )

    db = get_db()
    prof = db.execute("SELECT * FROM profiles WHERE id = ?", (requested_id,)).fetchone()

    return render_template(
        "secure_profile.html",
        profile=prof,
        blocked=False,
        session_user=session["username"],
    )


# ── Logs demo — Blue Team ─────────────────────────────────────────────────────

@app.route("/logs-demo")
def logs_demo():
    entries = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            entries = f.readlines()[-60:]
    return render_template("logs_demo.html", log_entries=entries)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        from init_db import init_db
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
