import sqlite3
import hashlib
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

DB_PATH    = os.path.join(os.path.dirname(__file__), "database.db")
_M3_FLAG   = os.environ.get("CTF_M3_FLAG",   "picoCTF{REPLACE_ME_M3}")
_CASE_CODE = os.environ.get("CTF_CASE_CODE", "REPLACE_ME")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def init_db():
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS cases;
        DROP TABLE IF EXISTS profiles;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id            INTEGER PRIMARY KEY,
            username      TEXT    NOT NULL UNIQUE,
            password      TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'employee'
        );

        CREATE TABLE profiles (
            id           INTEGER PRIMARY KEY,
            user_id      INTEGER,
            name         TEXT    NOT NULL,
            department   TEXT    NOT NULL,
            access_level TEXT    NOT NULL,
            note         TEXT    NOT NULL
        );

        CREATE TABLE cases (
            id            TEXT PRIMARY KEY,
            title         TEXT NOT NULL,
            status        TEXT NOT NULL,
            recovery_note TEXT NOT NULL,
            code_hash     TEXT
        );
    """)

    # --- Users ---
    # password column: plain text (intentionally insecure — used by VULNERABLE login route)
    # password_hash column: SHA-256 (used by SECURE login route for comparison)
    c.execute(
        "INSERT INTO users (id, username, password, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (1, "admin", "AtlasCore@2024!", sha256("AtlasCore@2024!"), "admin"),
    )
    c.execute(
        "INSERT INTO users (id, username, password, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (102, "maya", "employee123", sha256("employee123"), "employee"),
    )

    # --- Profiles ---
    # Admin profile: note references the case record instead of containing the flag directly
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 1, "Avery Stone", "Security Engineering", "Administrator",
         "Recovery note archived under case AC-731. Access requires case verification code."),
    )
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (102, 102, "Maya Chen", "Customer Operations", "Employee",
         "Standard employee profile — no sensitive data."),
    )

    # Decoy profiles (IDs chosen to misdirect enumeration)
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (2, None, "Legacy Account", "Operations", "Employee",
         "Account deactivated. No sensitive data. Contact IT to reactivate."),
    )
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (207, None, "Batch 207 Archive", "Infrastructure", "Employee",
         "Standard batch archive — audit ref BLUECORE-207. No active assignment."),
    )
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (404, None, "Deleted Account", "Unknown", "Revoked",
         "Account removed from system. Contact security-ops for reinstatement."),
    )

    # --- Cases ---
    # Decoy cases accessible without a code
    c.execute(
        "INSERT INTO cases (id, title, status, recovery_note, code_hash) VALUES (?, ?, ?, ?, ?)",
        ("AC-100", "Standard Audit Case", "Resolved",
         "No anomalies detected during routine review. Closed per standard protocol.", None),
    )
    c.execute(
        "INSERT INTO cases (id, title, status, recovery_note, code_hash) VALUES (?, ?, ?, ?, ?)",
        ("AC-404", "Connectivity Review", "Pending",
         "Route analysis pending external review. Escalate to ops-lead for clearance.", None),
    )
    # Restricted case — requires SHA256(_CASE_CODE) to access
    c.execute(
        "INSERT INTO cases (id, title, status, recovery_note, code_hash) VALUES (?, ?, ?, ?, ?)",
        ("AC-731", "Security Recovery Case", "Restricted",
         _M3_FLAG, sha256(_CASE_CODE)),
    )

    conn.commit()
    conn.close()
    print(f"[+] Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
