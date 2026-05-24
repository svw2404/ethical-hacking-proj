# Presentation Notes — Operation Digital Turf War

Use this document to prepare your slides and talking points. The structure below maps to the 14-slide presentation format.

---

## Slide 1 — Title

**Title:** Operation Digital Turf War  
**Subtitle:** Mini CTF Ethical Hacking Project  
**Include:** Team member names, course name, instructor name, date

**Speaking note:**  
Introduce the project name and the fictional scenario: two cyber-intelligence units competing for control of a restricted digital network. Explain that this is a 3-stage CTF lab where one group attacks and the other defends and designs.

---

## Slide 2 — Project Overview

**Bullet points:**
- Three-stage Capture-the-Flag lab (Easy / Medium / Hard)
- Red Team vs Blue Team model
- Hosted in a controlled VM or Docker environment
- Covers: Web vulnerabilities, Encoding/Crypto, Network reconnaissance, and Blue Team defense

**Speaking note:**  
Explain the Red Team / Blue Team split. Red Team attacks and captures flags. Blue Team designs the challenges, explains the vulnerabilities, and demonstrates the secure fix. Both roles are required for a complete score.

---

## Slide 3 — Assignment Requirement Mapping

**Table:**

| Requirement | Our Implementation |
|-------------|-------------------|
| Easy Challenge (100 pts) | Mission 1 — Staff Portal Leak |
| Medium Challenge (200 pts) | Mission 2 — Layered Transmission |
| Hard Challenge (300 pts) | Mission 3 — Digital Turf Breach |
| Web Vulnerability | HTML info disclosure + SQL Injection + IDOR |
| Network Vulnerability | nmap scan, exposed Flask service on port 5000 |
| Encoding / Crypto Challenge | Base64 + Reverse + Caesar cipher chain |
| Blue Team Defense | Secure comparison, logs, rate limiting |

**Speaking note:**  
Show that every rubric requirement is satisfied. Point out that the project is not three static pages — it is a real Flask application with a database, intentional vulnerabilities, and secure alternatives.

---

## Slide 4 — System Architecture

**Diagram:**

```
Red Team Machine
      |
      | nmap / browser / Burp Suite
      v
Assigned Ethical VM (or Docker on laptop)
      |
      | Flask Web App — Port 5000
      v
SQLite Database
      |
      +── Vulnerable routes: /login, /profile
      +── Secure routes: /secure-login, /secure-profile
      +── Logs: /logs-demo → access.log
```

**Deployment options:**
- Local: `python app/app.py`
- Docker: `docker compose up --build`
- Shared on demo day: ngrok exposes port 5000 (browser/Burp only — not nmap)

**Speaking note:**  
Explain that Docker gives any machine a consistent, one-command environment. The app runs on port 5000 so nmap can discover it on the assigned VM. ngrok is for HTTP sharing only — nmap goes against the actual VM IP, not the ngrok domain.

---

## Slide 5 — Mission 1: Staff Portal Leak

**Fields:**
- Difficulty: Easy — 100 pts
- Category: Web / Information Disclosure
- Concept: Sensitive data in HTML comments
- Technique: View Page Source / Browser DevTools
- OWASP: A05:2021 — Security Misconfiguration

**Speaking note:**  
Explain what HTML comments are and why they are dangerous. The rendered page looks completely normal. But pressing Ctrl+U reveals the page source, which includes everything sent by the server — including comments that developers forget to remove before going live. This is the simplest challenge by design. It teaches one foundational rule: anything delivered to the browser is visible to the user.

**Screenshot to show:** Page source with the flag visible in the HTML comment.

---

## Slide 6 — Mission 2: Layered Transmission

**Fields:**
- Difficulty: Medium — 200 pts
- Category: Encoding / Cryptography
- Concept: Encoding is not encryption
- Technique: Base64 decode → string reversal → Caesar shift −3
- OWASP: A02:2021 — Cryptographic Failures

**Encoding chain (Blue Team design):**
```
Original flag
→ Caesar cipher (+3)
→ Reverse string
→ Base64 encode
→ Displayed on page as payload
```

**Decoding chain (Red Team solution):**
```
Payload
→ Base64 decode
→ Reverse string
→ Caesar cipher (−3)
→ Flag
```

**Speaking note:**  
Explain the difference between encoding and encryption. Base64 is a format transformation — anyone can reverse it with no key. Caesar cipher is a substitution — anyone can reverse it by trying 25 combinations. Layering three reversible operations does not produce real security. Real encryption (AES-256) requires a secret key and is computationally infeasible to reverse without it.

**Screenshot to show:** CyberChef or Python terminal showing the three decode steps and the final flag.

---

## Slide 7 — Mission 3: Digital Turf Breach

**Fields:**
- Difficulty: Hard — 300 pts
- Category: Web + Network + Database + Blue Team Defense
- Concepts: Network scanning, SQL Injection, IDOR / Broken Access Control
- Tools: nmap, browser, Burp Suite
- OWASP: A01, A03, A07, A09

**Attack flow summary:**
1. nmap discovers Flask on port 5000
2. SQL injection bypasses the login form
3. IDOR exposes the admin profile
4. Flag captured from admin's notes field

**Speaking note:**  
This is the hardest mission because it chains three techniques. The student must first find the service (reconnaissance), then break authentication (SQL injection), then escalate access (IDOR). Each step teaches a distinct real-world vulnerability. The Blue Team then demonstrates the fix for all three.

**Screenshots to show:** nmap output, login with payload entered, admin profile with flag, log entries.

---

## Slide 8 — Vulnerable vs Secure Comparison

**Table:**

| Feature | Vulnerable Version | Secure Version |
|---------|-------------------|----------------|
| SQL Query | String concatenation | Parameterized query |
| Password Storage | Plain text | SHA-256 hash |
| Access Control | Trusts `?id=` parameter | Checks `session["user_id"]` |
| Error Messages | Exposes raw SQL query | Generic message only |
| Rate Limiting | None | 5 attempts / 60 seconds |
| Logging | Minimal | All suspicious events logged |
| SQLi attack | Succeeds | Blocked and logged |
| IDOR attack | Succeeds | Returns 403 Forbidden |

**Speaking note:**  
The secure version is not a different application — it is the same scenario with correct implementation. Walk through each row. Emphasize that the fixes are not complex: parameterized queries are one line different from the vulnerable version. The biggest risk is not knowing the correct pattern.

---

## Slide 9 — Red Team Attack Flow

**Sequential steps:**

```
1. nmap -sV <target-ip>
      ↓ discovers port 5000 / Flask
2. Open /login in browser
      ↓
3. Enter SQL injection payload in username field
      ↓ authentication bypassed
4. Redirected to admin profile
      ↓
5. Notes field contains the final flag
      ↓
6. Document all steps + screenshots
      ↓
7. Submit flag + write-up + mitigation suggestion
```

**Speaking note:**  
Walk through each step during the demo. Show the nmap scan result. Show the login form with the payload. Show the profile page with the flag visible. If time allows, show `/logs-demo` so the class can see how the attack was recorded.

---

## Slide 10 — Blue Team Defense Flow

**Sequential steps:**

```
1. Designed the challenge environment (Flask + SQLite)
      ↓
2. Identified intentional vulnerabilities (SQLi + IDOR)
      ↓
3. Implemented logging for all suspicious events
      ↓
4. Built secure comparison routes
      ↓
5. Demonstrated that attack fails on secure version
      ↓
6. Documented root cause and mitigation
      ↓
7. Prepared hardening plan
```

**Speaking note:**  
The Blue Team's job is not just to design puzzles — it is to understand why each vulnerability exists, how it is exploited, and exactly what code change eliminates it. Show the secure login blocking the SQL injection payload. Show the secure profile returning 403. Show the log entries. This is the defense mindset.

---

## Slide 11 — Course Chapter Connections

**List:**

| Topic | Where It Appears |
|-------|-----------------|
| OWASP Injection (SQLi) | Mission 3 — vulnerable login |
| OWASP Broken Access Control (IDOR) | Mission 3 — vulnerable profile |
| OWASP Sensitive Data Exposure | Mission 1 — HTML comments |
| OWASP Cryptographic Failures | Mission 2 — encoding vs encryption |
| OWASP Security Misconfiguration | Mission 1 — debug data in production |
| OWASP Logging & Monitoring Failures | Logs Demo |
| Reconnaissance / Network Scanning | Mission 3 — nmap |
| Ethical hacking methodology | All missions — authorization, scope, reporting |
| Penetration testing methodology | Pre-engagement, recon, exploitation, reporting |

**Speaking note:**  
Every technical element of this project maps directly to what was taught in class. This is not a standalone exercise — it applies the exact concepts from the OWASP, web security, and ethical hacking chapters to a real working system.

---

## Slide 12 — Screenshots and Demo

**Checklist of screenshots to include:**

- [ ] **Home page** — mission dashboard showing all three mission cards at `http://<target>:5000`
- [ ] **Mission 1** — login page rendered in the browser (flag is NOT visible)
- [ ] **Mission 1** — View Page Source with the HTML comment and flag highlighted
- [ ] **Mission 2** — the encoded payload displayed on the challenge page
- [ ] **Mission 2** — CyberChef or Python terminal showing each decode step and the final flag
- [ ] **Mission 3** — `nmap -sV <vm-ip>` output showing port 5000 open (VM/LAN deployment only)
- [ ] **Mission 3** — login page with the SQL injection payload (`maya' --`) entered in the username field
- [ ] **Mission 3** — Maya's employee profile at `/profile?id=102` (no flag — shows why IDOR is needed)
- [ ] **Mission 3** — URL bar changed to `/profile?id=1` and admin profile page with flag visible
- [ ] **Mission 3** — secure login page with the same SQLi payload rejected and generic error shown
- [ ] **Mission 3** — secure profile returning the 403 blocked page when `?id=1` is attempted
- [ ] **Logs demo** — `/logs-demo` showing INFO and WARNING entries from the full attack session

**Speaking note:**  
Screenshots are evidence. Each one should show a specific step clearly. Use Burp Suite's HTTP history to show the raw POST request with the payload if available — it makes the injection more concrete for the audience.

---

## Slide 13 — Ethical Considerations

**Bullet points:**

- All attacks performed only against the assigned lab VM or localhost
- No denial-of-service attacks, no network flooding
- No scanning of external systems or the ngrok domain
- No real malware, no destructive payloads
- Tools used only within authorized scope: nmap, Burp Suite, CyberChef, browser
- ngrok used only for HTTP sharing — not as a scan target
- All activity is educational simulation in a controlled environment
- Flags captured by exploiting challenges — not looked up or shared early

**Speaking note:**  
Ethical hacking requires written authorization and a defined scope. Our scope is this lab VM only. Every technique demonstrated here is legal within that scope and illegal outside of it. The rate limiter, the logs, and the secure versions all exist to demonstrate what real defensive systems do — this is the other side of ethical hacking.

---

## Slide 14 — Conclusion

**Key takeaways:**

- Three real vulnerabilities demonstrated on a real backend system
- Not static HTML — Flask + SQLite + Docker Compose
- Both the attack path and the defensive fix are shown side by side
- Logging captures what a real attacker's activity looks like
- The project covers six OWASP Top 10 categories
- Designed to satisfy every rubric requirement while teaching real skills

**Closing line:**  
Operation Digital Turf War demonstrates that the gap between a vulnerable system and a secure one is often just a few lines of code — but understanding why those lines matter is the entire point of ethical hacking.

---

## Source Code Sharing Policy

> **Important:** Do not share the GitHub repository or any source files with Red Team players before the lab session ends.
> 
> Give players only:
> - The running URL (`http://<vm-ip>:5000` or the ngrok URL)
> - `PLAYER_GUIDE.md`
>
> The source code contains flag locations, vulnerability implementations, and credential data. Sharing it before play ends is equivalent to handing out the answer key.
>
> Share the repository only after all flags have been submitted and the lab session is closed.

---

## Demo Order (Suggested)

1. Open home page — show mission cards
2. Mission 1 — Ctrl+U on the portal page → flag in source
3. Mission 2 — show payload, run Python decode live
4. Mission 3 — run nmap, enter SQLi payload, show admin profile + flag
5. Secure login — show the same payload failing
6. Secure profile — show 403 blocked page
7. Logs demo — show WARNING entries from the attack session

Total demo time: approximately 8–12 minutes depending on live speed.
