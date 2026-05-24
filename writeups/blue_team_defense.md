# Blue Team Defense — Operation Digital Turf War

**Team Name:** [Your Team Name]  
**Date:** [Date of Lab]  
**Instructor:** [Instructor Name]  
**Course:** Ethical Hacking / Information Security

---

## System Design Overview

### Architecture

```
Red Team Machine
      |
      | nmap / browser / Burp Suite
      v
Assigned Ethical VM — Flask App (Port 5000)
      |
      +──── /mission1 ──── HTML comment challenge (static page)
      |
      +──── /mission2 ──── Encoded payload challenge (server-generated)
      |
      +──── /login ──────── VULNERABLE: SQLi login → IDOR profile
      |
      +──── /secure-login ── SECURE: parameterized, hashed, rate-limited
      |
      +──── /logs-demo ───── Blue Team logging demonstration
      v
SQLite Database (users, profiles tables)
      |
      +── Vulnerable version: plain passwords, concatenated SQL
      +── Secure version: SHA-256 hashes, parameterized queries, session auth
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python Flask 3.0 |
| Database | SQLite |
| Frontend | HTML5, CSS3, vanilla JS |
| Deployment | Docker Compose / Ubuntu VM |
| Logging | Python logging module → access.log |

---

## Mission 1 — Blue Team Design

### Intentional Vulnerability

**Type:** Sensitive Data Exposure via HTML Comment  
**Difficulty:** Easy  
**OWASP:** A05:2021 — Security Misconfiguration

**Design decision:** The flag is placed inside an HTML comment tag (`<!-- -->`). This simulates a real developer mistake where debug notes are left in production code. The comment is invisible in the rendered browser view but fully visible in the page source.

### Expected Exploitation Path

1. Player opens `/mission1`.
2. Player presses Ctrl+U or right-clicks → View Page Source.
3. Player searches for the flag in the HTML comment.
4. Flag captured.

### Detection Strategy

In the vulnerable version, there is no way to detect this — because the player reads source code locally in their browser. No server request is needed.

**Blue Team lesson:** This demonstrates why security cannot rely on "the user won't look at the source." Source code inspection is a basic technique available to every user.

### Hardening Plan

| Action | Description |
|--------|-------------|
| Remove comments | Delete all HTML comments before deployment |
| Code review | Add source-code comment inspection to CI/CD pipeline |
| Server-side secrets | Store flags and credentials in environment variables |
| Static analysis | Use tools like `grep` or ESLint to catch embedded secrets |

---

## Mission 2 — Blue Team Design

### Intentional Vulnerability

**Type:** Cryptographic Failure — encoding used as encryption  
**Difficulty:** Medium  
**OWASP:** A02:2021 — Cryptographic Failures

**Design decision:** The flag is "hidden" using three reversible transformations applied in sequence: Caesar cipher (+3), string reversal, Base64 encoding. All three can be reversed without any key using free public tools like CyberChef or Python's standard library.

### Encoding Process Applied

```
picoCTF{layered_encoding_is_not_crypto}
→ Caesar +3 →
slfrFWI{odbhuhg_hqfrglqj_lv_qrw_fubswr}
→ Reverse →
}rwsbuf_wrq_vl_jqlgrfqh_ghuhbdo{IWFfrls
→ Base64 →
<payload displayed on page>
```

The payload is generated server-side in `app.py` at startup — always mathematically correct.

### Expected Exploitation Path

1. Player reads the encoded payload on `/mission2`.
2. Player identifies Base64 encoding.
3. Player decodes Base64, reverses the result, applies Caesar −3.
4. Flag recovered.

### Detection Strategy

Base64 and Caesar cipher are not encryption. There is nothing to detect — any party who sees the payload can decode it. This is the key lesson of this challenge.

### Hardening Plan

| Action | Description |
|--------|-------------|
| Use real encryption | AES-256-GCM for symmetric encryption |
| Key management | Store keys in a secure vault, not in the application |
| Avoid encoding as secrecy | Never treat Base64/Hex/ROT13 as confidentiality mechanisms |
| Encrypt in transit | Use TLS 1.2+ for all data transmission |

---

## Mission 3 — Blue Team Design

### Intentional Vulnerabilities

**Vulnerability 1: SQL Injection**  
**Type:** OWASP A03:2021 — Injection  
**Location:** `/login` POST handler  

**Vulnerable code:**
```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
db.execute(query)
```

The user input is concatenated directly into the SQL string. The single quote character breaks out of the string literal and allows the attacker to inject arbitrary SQL conditions.

---

**Vulnerability 2: IDOR / Broken Access Control**  
**Type:** OWASP A01:2021 — Broken Access Control  
**Location:** `/profile` GET handler  

**Vulnerable code:**
```python
profile_id = request.args.get("id")
user = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
return render_template("profile.html", profile=user)
```

The backend returns any profile whose `id` matches the URL parameter, without verifying that the requesting user is authorized to view that profile.

---

**Additional intentional weaknesses:**
- Passwords stored in plain text in the `password` column (visible in `init_db.py`)
- Error messages disclose the raw SQL query on failure (information disclosure)
- No rate limiting on the vulnerable login

### Expected Exploitation Path

1. `nmap -sV <target-ip>` → discovers Flask on port 5000
2. `/login` → SQL injection payload (`maya' --`) → session as Maya (id=102, employee)
3. `/profile?id=102` → normal employee profile visible, no flag
4. Change URL to `/profile?id=1` → IDOR: backend returns admin profile without authorization check
5. Admin profile note field contains the flag

> Alternative payload `' OR '1'='1' --` logs in directly as admin (skips step 3–4).
> The preferred intended path uses `maya' --` so both SQLi and IDOR are exercised.

### Detection and Logging Evidence

The logging system (`app/logs/access.log`) captures:

```
[INFO]    Login attempt  username=maya  ip=192.168.56.12
[WARNING] SQL injection payload detected  ip=192.168.56.12  payload_user="' OR '1'='1' --"
[INFO]    Login success  username=admin  ip=192.168.56.12
[WARNING] Profile IDOR  session_user=1  requested_profile=1  ip=192.168.56.12
```

View live logs at `/logs-demo`.

### IDS / Monitoring Strategy

| Event | Log Level | Action Recommended |
|-------|-----------|-------------------|
| SQL injection signature in input | WARNING | Alert security team, block IP after N events |
| Login failure | WARNING | Count failures; lock account after 5 attempts |
| IDOR access (profile mismatch) | WARNING | Alert; log for audit trail |
| Rate limit exceeded | WARNING | Block IP temporarily |
| DB error (malformed query) | ERROR | Immediate alert; could indicate active attack |

### Hardening Plan

**SQL Injection:**
```python
# Use parameterized queries — user input is a parameter, never SQL syntax
user = db.execute(
    "SELECT * FROM users WHERE username = ?", (username,)
).fetchone()
if user and user["password_hash"] == sha256(password):
    # authenticate
```

**Password Storage:**
```python
# Store SHA-256 hash (minimum); use bcrypt/argon2 in production
import hashlib
password_hash = hashlib.sha256(password.encode()).hexdigest()
```

> **Important note on SHA-256:** This lab uses SHA-256 for educational simplicity only.
> SHA-256 without a random salt is vulnerable to GPU-accelerated dictionary attacks and
> rainbow table lookups. In any real system, use **bcrypt**, **Argon2**, or **PBKDF2**,
> which include per-password salts and configurable cost factors that resist brute-force attacks.

**IDOR Fix:**
```python
# Always verify authorization server-side before returning data
requested_id = request.args.get("id")
if requested_id != str(session["user_id"]) and session["role"] != "admin":
    return "Access denied", 403
```

**Rate Limiting:**
```python
# Track failed attempts per IP; block after threshold
if is_rate_limited(ip):
    return "Too many attempts. Please wait.", 429
```

### Patch Strategy

| Component | Current State (Vulnerable) | Patched State (Secure) |
|-----------|---------------------------|------------------------|
| SQL Query | String concatenation | Parameterized query |
| Password Storage | Plain text | SHA-256 hash |
| Access Control | Trusts URL parameter | Session authorization check |
| Error Messages | Exposes raw SQL | Generic message |
| Rate Limiting | None | 5 attempts / 60 seconds |
| Logging | None | Full event logging |

### Long-term Defense Plan

1. **Input validation:** Validate and sanitize all user input at the boundary.
2. **Least privilege:** Database accounts should only have SELECT permission on needed tables.
3. **Regular security testing:** Run automated SAST/DAST tools on every deployment.
4. **Dependency monitoring:** Track Flask and SQLite CVEs; update promptly.
5. **SIEM integration:** Forward logs to a centralized SIEM for correlation and alerting.
6. **Access control reviews:** Regularly audit who can access what data.
7. **Penetration testing:** Commission annual pen tests on production systems.

---

## Vulnerable vs Secure Comparison

| Feature | Vulnerable (`/login`, `/profile`) | Secure (`/secure-login`, `/secure-profile`) |
|---------|-----------------------------------|--------------------------------------------|
| SQL query | String concatenation | Parameterized |
| Password storage | Plain text | SHA-256 hash |
| Access control | Trusts `?id=` parameter | Checks `session["user_id"]` |
| Error message | Exposes raw SQL | Generic "Invalid credentials" |
| Rate limiting | None | 5 attempts / 60 seconds per IP |
| Logging | Minimal | All suspicious events logged |
| SQLi attack | **Succeeds** | **Blocked** |
| IDOR attack | **Succeeds** | **Returns 403 Forbidden** |

---

## OWASP Coverage

| OWASP Category | Challenge | How It Applies |
|----------------|-----------|----------------|
| A01 — Broken Access Control | Mission 3 | IDOR on profile endpoint |
| A02 — Cryptographic Failures | Mission 2 | Encoding used as encryption |
| A03 — Injection | Mission 3 | SQL injection in login |
| A05 — Security Misconfiguration | Mission 1 | Sensitive data in HTML comments |
| A07 — Auth Failures | Mission 3 | Weak/plain passwords, no session management |
| A09 — Logging & Monitoring Failures | All | Logs demo; insufficient logging in vulnerable version |
