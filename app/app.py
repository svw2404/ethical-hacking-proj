import os
import re
import sqlite3
import hashlib
import base64
import logging
import time
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

from flask import (
    Flask, render_template, request, session,
    redirect, url_for, g, Response, make_response,
)

app = Flask(__name__)
app.secret_key = os.environ.get("CTF_MASTER_SEED", "atlas-core-dev-key-changeme")

BASE_DIR = os.path.dirname(__file__)
DB_PATH  = os.path.join(BASE_DIR, "database.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "access.log")

# ── Load flags and runtime secrets from environment ───────────────────────────
_M1_FLAG       = os.environ.get("CTF_M1_FLAG",   "picoCTF{REPLACE_ME_M1}")
_M2_FLAG       = os.environ.get("CTF_M2_FLAG",   "picoCTF{REPLACE_ME_M2}")
_INSTANCE_SEED = os.environ.get("CTF_INSTANCE_SEED", "")
_TEAM_ID       = os.environ.get("CTF_TEAM_ID",       "ops")

# Case code: explicit override wins; otherwise derived from CTF_INSTANCE_SEED so
# each deployed instance produces a different code — static analysis of the source
# or old screenshots cannot determine the correct code for the running instance.
_derived_case = (
    hashlib.sha256(f"case_code:{_INSTANCE_SEED}".encode()).hexdigest()[:12]
    if _INSTANCE_SEED else "REPLACE_ME"
)
_CASE_CODE = os.environ.get("CTF_CASE_CODE") or _derived_case

# ── Mission 1 — split flag into 4 base64 fragments ────────────────────────────
_q     = len(_M1_FLAG) // 4
_parts = [_M1_FLAG[:_q], _M1_FLAG[_q:2*_q], _M1_FLAG[2*_q:3*_q], _M1_FLAG[3*_q:]]
FRAG_A = base64.b64encode(_parts[0].encode()).decode()   # served in /archive/staff_audit_731.txt
FRAG_B = base64.b64encode(_parts[1].encode()).decode()   # injected in CSS comment
FRAG_C = base64.b64encode(_parts[2].encode()).decode()   # sent as X-Atlas-Audit response header
FRAG_D = base64.b64encode(_parts[3].encode()).decode()   # set as audit_hint cookie

# ── Mission 2 — key derived from operational metadata, complex encoding chain ─
# Key material comes from artifacts discoverable in Mission 1
_key_bytes = hashlib.sha256(b"ATLAS:BATCH-731").digest()[:8]

_fb         = _M2_FLAG.encode()
_xored      = bytes([_fb[i] ^ _key_bytes[i % 8] for i in range(len(_fb))])
_even_b     = bytes(_xored[i] for i in range(0, len(_xored), 2))
_odd_b      = bytes(_xored[i] for i in range(1, len(_xored), 2))
_transposed = _even_b + _odd_b
_rev_hex    = _transposed.hex()[::-1]
MISSION2_PAYLOAD = base64.b64encode(_rev_hex.encode()).decode()

# ── Mission 2 — decoy transmissions ──────────────────────────────────────────
# 731-A: simple base64; decodes to plaintext containing the Mission 3 case code
_decoy_a_text = (
    f"AtlasCore Ops // Batch 731 status nominal"
    f" // Team: {_TEAM_ID}"
    f" // Case AC-731 verification token: {_CASE_CODE}"
    f" // Comms secure."
)
DECOY_A = base64.b64encode(_decoy_a_text.encode()).decode()

# 731-C: simple base64; decodes to plausible but irrelevant ops message
_decoy_c_text = (
    "SYSTEM: Checkpoint alpha complete."
    " ATLAS subsystem authenticated. Proceed to Phase 2."
)
DECOY_C = base64.b64encode(_decoy_c_text.encode()).decode()

# ── Logging ───────────────────────────────────────────────────────────────────
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
_file_handler = logging.FileHandler(LOG_PATH)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger = logging.getLogger("ctf")
logger.setLevel(logging.INFO)
if not logger.handlers:
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
_WINDOW = 60
_MAX    = 5

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < _WINDOW]
    if len(_attempts[ip]) >= _MAX:
        return True
    _attempts[ip].append(now)
    return False

# ── SQLi pattern detector (logging only — not a WAF) ─────────────────────────
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


# ── Standard crawler discovery endpoints ─────────────────────────────────────

@app.route("/robots.txt")
def robots_txt():
    content = (
        "User-agent: *\n"
        "Disallow: /internal/\n"
        "Disallow: /archive/\n"
        "Disallow: /ops-notes/\n"
    )
    return Response(content, mimetype="text/plain")


# ── Dynamic CSS — fragment B injected as a deployment metadata comment ────────

@app.route("/assets/style.css")
def serve_css():
    static_css = os.path.join(BASE_DIR, "static", "css", "style.css")
    with open(static_css, "r") as f:
        css = f.read()
    comment = f"/* deployment-fragment-b: {FRAG_B} */\n"
    resp = make_response(comment + css)
    resp.headers["Content-Type"] = "text/css"
    return resp


# ── Archive directory — exposed deployment artifact zone ─────────────────────

@app.route("/archive/")
@app.route("/archive")
def archive_index():
    listing = (
        "Index of /archive/\n\n"
        "      Name                         Last modified    Size\n"
        "      ----                         -------------    ----\n"
        "      staff_audit_731.txt          2024-03-15       2.1K\n"
        "      staff_audit_old.txt          2023-11-02       1.8K\n"
        "      backup_notes.txt             2024-01-20       0.9K\n"
        "      checksum_manifest.txt        2024-03-15       0.4K\n"
    )
    return Response(listing, mimetype="text/plain")


@app.route("/archive/staff_audit_731.txt")
def archive_audit_731():
    content = (
        "Atlas Core Staff Audit — Redacted\n"
        "Classification: INTERNAL USE ONLY\n\n"
        "Batch: BATCH-731\n"
        "Coordinator: maya (id: 102)\n"
        "Personnel reviewed: 47\n"
        "Accounts flagged: 3\n"
        "Project keyword: ATLAS\n"
        "Audit Reference: BATCH-731\n\n"
        "Deployment metadata fragment:\n"
        f"{FRAG_A}\n\n"
        "Note: Remaining deployment fragments were distributed across operational channels.\n"
        "For full audit verification, contact atlas-ops.\n"
    )
    return Response(content, mimetype="text/plain")


@app.route("/archive/staff_audit_old.txt")
def archive_audit_old():
    content = (
        "Atlas Core Staff Audit — ARCHIVE COPY\n"
        "Classification: INTERNAL — SUPERSEDED\n\n"
        "Batch: BATCH-406 (EXPIRED)\n"
        "Project keyword: BLUECORE\n"
        "Coordinator: legacy-ops\n\n"
        "Token (expired):\n"
        "dGhpc190b2tlbl9oYXNfZXhwaXJlZA==\n\n"
        "Note: This document has been superseded. Refer to current audit batch.\n"
    )
    return Response(content, mimetype="text/plain")


@app.route("/archive/backup_notes.txt")
def archive_backup_notes():
    content = (
        "Atlas Core — Backup Notes\n"
        "Classification: INTERNAL\n\n"
        "Project: BLUECORE (deprecated)\n"
        "Successor project: ATLAS (active)\n"
        "Contact: devops@internal\n\n"
        "Note: BLUECORE project keys expired 2023-10-01.\n"
        "All operational tokens re-keyed under ATLAS project.\n"
    )
    return Response(content, mimetype="text/plain")


@app.route("/archive/checksum_manifest.txt")
def archive_checksum_manifest():
    content = (
        "CHECKSUM MANIFEST — BATCH-731\n"
        "Generated: 2024-03-15\n\n"
        "staff_audit_731.txt   sha256: 7f3a2b9c1d4e6f8a...\n"
        "staff_audit_old.txt   sha256: 4e1c9d5f2b7a0c3e...\n"
        "backup_notes.txt      sha256: 8b2f1e3a6d9c4b7f...\n\n"
        "Manifest verified by: atlas-ops\n"
    )
    return Response(content, mimetype="text/plain")


# ── Mission 1 — Web Recon / Deployment Artifact ───────────────────────────────

@app.route("/mission1")
def mission1():
    resp = make_response(render_template("mission1.html"))
    resp.headers["X-Atlas-Audit"] = f"fragment-c={FRAG_C}"
    resp.set_cookie("audit_hint", FRAG_D, samesite="Lax", httponly=False)
    return resp


# ── Mission 2 — Layered Transmission ─────────────────────────────────────────

@app.route("/mission2")
def mission2():
    return render_template(
        "mission2.html",
        decoy_a=DECOY_A,
        payload=MISSION2_PAYLOAD,
        decoy_c=DECOY_C,
    )


# ── Mission 3 — VULNERABLE login ─────────────────────────────────────────────

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
        # Payload  maya' --  bypasses the password check for that account.
        # This is here to demonstrate OWASP A03 Injection for the CTF lab.
        # NEVER do this in production code.
        # ─────────────────────────────────────────────────────────────────────
        query = (
            f"SELECT * FROM users WHERE username='{username}'"
            f" AND password='{password}'"
        )
        debug_query = query

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


# ── Mission 3 — VULNERABLE profile (IDOR) ────────────────────────────────────

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
    # Backend trusts the ?id= parameter and returns any profile without
    # checking whether the logged-in user is authorized to view it.
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


# ── Mission 3 — Case record (broken access control on secondary resource) ──────

@app.route("/case")
def case_record():
    if "user_id" not in session:
        return redirect(url_for("login"))

    case_id = request.args.get("id", "").strip().upper()
    code    = request.args.get("code", "").strip()
    ip      = get_ip()

    if not case_id:
        return Response(
            "Case ID required. Use ?id=<case_id>",
            status=400, mimetype="text/plain"
        )

    db   = get_db()
    case = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()

    if not case:
        logger.info(f"[INFO]    Case lookup  id={case_id}  result=not_found  ip={ip}")
        return Response("Case record not found.", status=404, mimetype="text/plain")

    # ── INTENTIONALLY VULNERABLE ──────────────────────────────────────────────
    # Only checks the code hash — does NOT verify the logged-in user is
    # authorized to access this case record.  Any authenticated user who
    # supplies the correct code can retrieve any case, including restricted ones.
    # This demonstrates Broken Access Control (OWASP A01) on a secondary object.
    # ─────────────────────────────────────────────────────────────────────────
    if case["code_hash"]:
        if hashlib.sha256(code.encode()).hexdigest() != case["code_hash"]:
            logger.warning(
                f"[WARNING] Case access denied  case={case_id}"
                f"  user={session.get('username')}  ip={ip}"
            )
            return render_template("case_denied.html", case_id=case_id)

    logger.warning(
        f"[WARNING] Case record accessed  case={case_id}"
        f"  user={session.get('username')}  ip={ip}"
    )
    return render_template("case_record.html", case=case)


# ── Blue Team — secure login ──────────────────────────────────────────────────

@app.route("/secure-login", methods=["GET", "POST"])
def secure_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ip = get_ip()

        logger.info(f"[INFO]    Secure login attempt  username={username}  ip={ip}")

        if is_rate_limited(ip):
            logger.warning(f"[WARNING] Rate limit exceeded  ip={ip}")
            error = "Too many login attempts. Please wait 60 seconds."
            return render_template("secure_login.html", error=error)

        if looks_like_sqli(username) or looks_like_sqli(password):
            logger.warning(
                f"[WARNING] SQLi attempt BLOCKED at secure-login  ip={ip}"
                f"  payload={username!r}"
            )

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

        logger.warning(f"[WARNING] Secure login failed  username={username}  ip={ip}")
        error = "Invalid credentials."

    return render_template("secure_login.html", error=error)


@app.route("/secure-logout")
def secure_logout():
    session.clear()
    return redirect(url_for("secure_login"))


# ── Blue Team — secure profile (authorization check) ─────────────────────────

@app.route("/secure-profile")
def secure_profile():
    if "user_id" not in session or not session.get("secure_mode"):
        return redirect(url_for("secure_login"))

    requested_id = request.args.get("id", str(session["user_id"]))
    ip = get_ip()

    if requested_id != str(session["user_id"]) and session.get("role") != "admin":
        logger.warning(
            f"[WARNING] Secure profile: BLOCKED  session_user={session['user_id']}"
            f"  requested={requested_id}  ip={ip}"
        )
        return render_template(
            "secure_profile.html",
            profile=None,
            blocked=True,
            session_user=session["username"],
        )

    db   = get_db()
    prof = db.execute("SELECT * FROM profiles WHERE id = ?", (requested_id,)).fetchone()

    return render_template(
        "secure_profile.html",
        profile=prof,
        blocked=False,
        session_user=session["username"],
    )


# ── Blue Team — logs demo ─────────────────────────────────────────────────────

@app.route("/logs-demo")
def logs_demo():
    entries = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            entries = f.readlines()[-60:]
    return render_template("logs_demo.html", log_entries=entries)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from init_db import init_db
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
