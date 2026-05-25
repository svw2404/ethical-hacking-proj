# Operation Digital Turf War

A three-stage Capture-the-Flag cybersecurity lab for an Ethical Hacking / EMI university course.  
**Red Team vs Blue Team. Flask + SQLite. Intentional vulnerabilities. Secure comparisons. Full logging.**

> This repository contains intentional security vulnerabilities for educational purposes only.  
> All attacks must be performed exclusively within the authorized lab environment.  
> Do not attempt to attack external systems.

> **For Blue Team / Instructors:** Do not share the source code or this repository with Red Team players before the lab session ends. Give players only the running URL and `PLAYER_GUIDE.md`.
> The flags are not directly recoverable from the committed public repository alone; players must interact with the running app and collect runtime artifacts. Flags live only in `.env` (gitignored) and in the running application's memory — not in the committed source.
> Share the repository only after all flags have been submitted.

---

## Storyline

Two fictional cyber-intelligence units — **Atlas Core** and **BlueCore** — are competing for control of a restricted internal network known as the Digital Turf Zone.

The Red Team begins with access to a suspicious internal portal. They find evidence of careless deployment practices, decode an intercepted transmission using intelligence gathered from the first mission, scan the assigned lab server, and finally exploit a vulnerable employee portal. The Blue Team designed the challenges, explains each vulnerability, and demonstrates the secure fix.

---

## Missions

| Mission | Difficulty | Points | Category | Concept |
|---------|-----------|--------|----------|---------|
| Mission 1 — Hard Web Recon | Hard | 300 | Web Recon / Info Disclosure | Multi-source deployment artifact exposure, metadata leakage across 4 channels |
| Mission 2 — Hard Crypto/Encoding | Hard | 300 | Crypto / Encoding | Custom encoding chain with derived cross-mission key; 3 transmissions (one real) |
| Mission 3 — Digital Turf Breach | Hard | 300 | Web + Network | SQLi → IDOR → case record broken access control; code sourced from Mission 2 |
| **Total** | | **900** | | |

Each mission has a flag in the format `picoCTF{...}`. Flags are discovered by exploiting the challenge — they are not provided here.

---

## Assignment Mapping

| Requirement | Implementation |
|-------------|----------------|
| Hard Challenge (300 pts) | Mission 1 — Hard Web Recon |
| Hard Challenge (300 pts) | Mission 2 — Hard Crypto/Encoding |
| Hard Challenge (300 pts) | Mission 3 — Digital Turf Breach |
| Web Vulnerability | Missions 1 and 3 |
| Network Vulnerability | Mission 3 — service discovery via nmap |
| Encoding / Crypto Challenge | Mission 2 — multi-step encoding chain with cross-mission key |
| Blue Team Defense | Secure comparison routes, logging, rate limiting |

---

## Requirements

- Python 3.10+ **or** Docker Desktop
- Browser (Chrome or Firefox)
- `nmap` — for Mission 3 network reconnaissance (VM/LAN deployment only)
- Optional: Burp Suite, CyberChef, terminal

---

## Per-Instance Seed (Recommended)

Each deployed instance should use a unique `CTF_INSTANCE_SEED`. The app derives the Mission 3 case code from this seed at startup — so even if someone has the source code or screenshots from a different run, the case code they find will not work on your live instance.

```env
CTF_INSTANCE_SEED=<long-random-string>   # e.g. openssl rand -hex 16
CTF_TEAM_ID=team_blue_01                 # optional label, included in decoded transmissions
```

The database must be re-initialized after changing `CTF_INSTANCE_SEED` (restart the container or delete `app/database.db` and rerun `python app/init_db.py`).

---

## Setup — Run Locally (Python)

```bash
git clone <repo-url>
cd ethical-hacking-proj

# 1. Create your local .env from the template and fill in the real values
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
# (edit .env — replace every REPLACE_ME with the actual flag/seed values)

pip install -r requirements.txt
python app/app.py               # initializes the database automatically on first run
```

Open: `http://localhost:5000`

---

## Setup — Run with Docker (Recommended)

```bash
git clone <repo-url>
cd ethical-hacking-proj

# 1. Create your local .env from the template and fill in the real values
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
# (edit .env — replace every REPLACE_ME with the actual flag/seed values)

docker compose up --build
```

Open: `http://localhost:5000`

From a lab machine on the same network: `http://<host-ip>:5000`

---

## Network Reconnaissance (Mission 3)

Mission 3 includes a network scanning step. Use nmap against the assigned VM or LAN host:

```bash
nmap -sV <vm-ip>
```

This will discover the Flask web service running on port 5000, which is the intended entry point for Mission 3.

> **Important:** Run nmap only against the assigned lab VM or local machine IP.  
> Do not run nmap against the ngrok domain — see the ngrok note below.

---

## Demo Day Sharing (ngrok)

To share the lab with classmates who are on a different network, expose port 5000 using ngrok:

```bash
# Terminal 1: start the app
docker compose up --build

# Terminal 2: expose it
ngrok http 5000
```

ngrok will print a public URL such as `https://abc123.ngrok-free.app`. Share this URL.

**Important ngrok limitations:**

- Classmates should access the lab using a **browser or Burp Suite only** via the ngrok URL.
- **Do not run `nmap` against the ngrok domain.** The ngrok hostname points to ngrok's own infrastructure, not the actual target host. Scanning it is inaccurate and may scan third-party systems.
- For full Mission 3 network reconnaissance grading, use the **VM or LAN deployment** so students can run `nmap -sV <vm-ip>` against the real host IP.
- ngrok is suitable for HTTP access to all missions and for testing the web portions of Mission 3. It is not a substitute for VM-based network scanning.

---

## Routes

| Route | Description |
|-------|-------------|
| `/` | Mission dashboard |
| `/mission1` | Hard — Web Recon (also sets fragment header/cookie) |
| `/mission2` | Hard — Crypto/Encoding (three transmissions) |
| `/login` | Hard — Vulnerable login page |
| `/profile` | Hard — Employee profile page (IDOR) |
| `/case` | Hard — Internal case record (broken access control) |
| `/robots.txt` | Standard crawler hints (Mission 1 discovery path) |
| `/archive/` | Exposed deployment artifact directory (Mission 1) |
| `/assets/style.css` | Dynamic CSS (contains Mission 1 fragment B) |
| `/secure-login` | Blue Team — Secure login comparison |
| `/secure-profile` | Blue Team — Secure profile comparison |
| `/logs-demo` | Blue Team — Security logging demonstration |

---

## Allowed Tools

Red Team may use:

- Browser (Chrome or Firefox) and DevTools
- `nmap` — against assigned VM or local IP only
- Burp Suite — against the lab app only
- CyberChef — for encoding analysis
- Python 3 standard library
- Terminal / command line

Do not use automated exploitation tools (sqlmap, hydra, Metasploit) against the lab without instructor permission. Do not scan or interact with any system outside the assigned lab environment.

---

## Submission Checklist

Each team must submit:

- [ ] Attack flow diagram
- [ ] Vulnerability explanation for each mission
- [ ] Mitigation strategy for each mission
- [ ] List of tools used
- [ ] Screenshots of each step
- [ ] Flag for each mission (captured, not looked up)
- [ ] Red Team write-up (`writeups/red_team_writeup.md`)
- [ ] Blue Team defense explanation (`writeups/blue_team_defense.md`)

---

## Ethical Rules

- Attack **only** this assigned lab environment.
- No DoS attacks, no network flooding, no destructive payloads.
- No scanning or interacting with external systems.
- No real malware or self-propagating code.
- All work is for authorized educational purposes only.
- nmap must be run only against the assigned VM or localhost.
- ngrok URL must be accessed via browser or Burp Suite only — not scanned.

---

## Project Structure

```
ethical-hacking-proj/
├── README.md                  ← Player-facing overview (this file)
├── PLAYER_GUIDE.md            ← How to start, rules, submission format
├── PRESENTATION_NOTES.md      ← Slide structure and talking points
├── TEACHER_SOLUTION.md        ← Private: flags, payloads, credentials (not for players)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── app/
│   ├── app.py                 ← Flask app — all routes
│   ├── init_db.py             ← Database initialization
│   ├── logs/access.log        ← Security event log (auto-generated)
│   ├── templates/             ← HTML pages
│   └── static/                ← CSS, JS, and static assets
│
├── challenges/                ← Challenge Creator Forms (Blue Team)
├── writeups/                  ← Red/Blue Team write-up templates
└── screenshots/               ← Evidence captures (fill in during lab)
```

---

## OWASP Coverage

| OWASP Category | Mission |
|----------------|---------|
| A01:2021 — Broken Access Control | Mission 3 |
| A02:2021 — Cryptographic Failures | Missions 1 and 2 |
| A03:2021 — Injection | Mission 3 |
| A05:2021 — Security Misconfiguration | Missions 1 and 2 |
| A07:2021 — Identification and Auth Failures | Mission 3 |
| A09:2021 — Security Logging and Monitoring Failures | Logs Demo |

---

## Team

| Role | Name |
|------|------|
| Blue Team Lead | |
| Red Team Lead | |
| Developer | |
| Presenter | |
