import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def init_db():
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS profiles;

        CREATE TABLE users (
            id            INTEGER PRIMARY KEY,
            username      TEXT    NOT NULL UNIQUE,
            password      TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'employee'
        );

        CREATE TABLE profiles (
            id           INTEGER PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            name         TEXT    NOT NULL,
            department   TEXT    NOT NULL,
            access_level TEXT    NOT NULL,
            note         TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # --- Users ---
    # password column: plain text (intentionally insecure — used by the VULNERABLE login route)
    # password_hash column: SHA-256 (used by the SECURE login route)
    # The Blue Team explanation covers why plain storage is dangerous.
    c.execute(
        "INSERT INTO users (id, username, password, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (1, "admin", "AtlasCore@2024!", sha256("AtlasCore@2024!"), "admin"),
    )
    c.execute(
        "INSERT INTO users (id, username, password, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (102, "maya", "employee123", sha256("employee123"), "employee"),
    )

    # --- Profiles ---
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (
            1, 1,
            "Avery Stone",
            "Security Engineering",
            "Administrator",
            "Admin recovery note: picoCTF{digital_turf_war_compromised}",
        ),
    )
    c.execute(
        "INSERT INTO profiles (id, user_id, name, department, access_level, note) VALUES (?, ?, ?, ?, ?, ?)",
        (
            102, 102,
            "Maya Chen",
            "Customer Operations",
            "Employee",
            "Standard employee profile — no sensitive data.",
        ),
    )

    conn.commit()
    conn.close()
    print(f"[+] Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
