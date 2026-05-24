# Player Guide — Operation Digital Turf War

Welcome to the Operation Digital Turf War CTF lab. This guide explains how to get started, what you are allowed to do, and how to submit your findings.

> No flags, payloads, or solution steps are provided here. You must discover them yourself.

---

## Getting Started

### Option A — Lab VM (recommended for Mission 3)

Your instructor or Blue Team will provide the lab VM's IP address. Open a browser and go to:

```
http://<vm-ip>:5000
```

### Option B — Local Docker

If running the lab on your own machine:

```bash
docker compose up --build
```

Then open: `http://localhost:5000`

### Option C — Shared URL (ngrok)

If the Blue Team has shared a public ngrok link, open that URL in your browser. Note that network scanning only applies to VM/LAN deployments — see the Mission 3 notes below.

---

## Lab Overview

The home page at `/` shows the three missions. Start with Mission 1 and work upward.

Each mission has a challenge description, hints, and a Blue Team explanation. Read everything — context matters.

The lab also includes **secure comparison pages** that show the patched version of each vulnerable system. These are for Blue Team reference and learning.

---

## Mission 1 — Staff Portal Leak

**Difficulty:** Easy · 100 pts  
**Category:** Web / Information Disclosure  
**URL:** `/mission1`

A corporate login page. The login form does not accept credentials — that is not the goal.

Think about what information might be present in the page that the browser does not visibly display.

**Hints are available** on the page. Click to reveal them one at a time.

---

## Mission 2 — Layered Transmission

**Difficulty:** Medium · 200 pts  
**Category:** Encoding / Cryptography  
**URL:** `/mission2`

An intercepted transmission encoded in multiple layers. The page displays the encoded payload.

Your goal is to identify and reverse each transformation layer to recover the original message.

**Recommended tools:** CyberChef (free, browser-based), Python 3 standard library  
**Hints are available** on the page — reveal them only when stuck.

---

## Mission 3 — Digital Turf Breach

**Difficulty:** Hard · 300 pts  
**Category:** Web + Network  
**URL:** `/login` (entry point)

This is a multi-step challenge. Work through it in phases:

**Phase 1 — Reconnaissance**  
If using a VM or LAN deployment, start by scanning the target host:
```bash
nmap -sV <vm-ip>
```
Identify what service is running and on which port.

> If using the ngrok URL: skip nmap. Open the URL in your browser or Burp Suite.  
> Do not run nmap against the ngrok domain — it does not represent the real target.

**Phase 2 — Authentication**  
Access the login page and test it for vulnerabilities. Think about how web login forms communicate with databases. What happens if the input is not properly validated?

**Phase 3 — Access Control**  
After logging in, observe the URL carefully. Think about whether the application verifies that you are authorized to view the data it returns.

**Recommended tools:** nmap, browser, Burp Suite, DevTools

---

## Allowed Tools

| Tool | Allowed |
|------|---------|
| Browser DevTools (F12 / Ctrl+U) | ✅ Yes |
| nmap | ✅ Yes — assigned VM or localhost only |
| Burp Suite | ✅ Yes — lab app only |
| CyberChef | ✅ Yes |
| Python 3 (standard library) | ✅ Yes |
| curl / wget | ✅ Yes — lab app only |
| sqlmap / Metasploit / hydra | ⚠ Only with instructor permission |
| External websites / APIs | ❌ No |
| Any system not in the lab | ❌ No |

---

## What You Cannot Do

- Do not run nmap or any scanner against external hosts or the ngrok domain.
- Do not attempt denial-of-service attacks.
- Do not modify or delete the database, logs, or application files.
- Do not share flags with other groups before the lab ends.
- Do not look up flags — capture them by exploiting the challenge.

---

## How to Submit

For each mission, submit the following:

### Flag
The string in the format `picoCTF{...}` that you discovered by exploiting the challenge.

### Write-up (per mission)
Using the template in `writeups/red_team_writeup.md`, fill in:

- Initial analysis — what you observed when you first opened the challenge
- Tools used — list every tool you actually used
- Exploitation steps — exact commands, payloads, or actions taken
- Flag found — the captured flag string
- Mitigation suggestion — how this vulnerability should be fixed

### Screenshots
Capture screenshots of each key step. At minimum:

**Mission 1:** Page source with the flag visible  
**Mission 2:** Decode process and final flag output  
**Mission 3:** nmap result, login attempt, profile page with flag, and the log page showing your activity

Place screenshots in the corresponding `screenshots/mission1/`, `screenshots/mission2/`, `screenshots/mission3/` folders.

### Attack Flow Diagram
A simple diagram showing your attack steps in sequence. Can be drawn, ASCII, or a diagram tool. Include it in your write-up.

---

## Blue Team Players

If you are on the Blue Team, your deliverables are in `writeups/blue_team_defense.md`. Fill in:

- System design explanation — what you built and why
- Intentional vulnerability — what the bug is and where it lives in the code
- Expected exploitation path — how a Red Team player would exploit it
- Detection and logging evidence — show log entries from `/logs-demo`
- Mitigation strategy — the specific fix, with example code
- Secure version explanation — describe what the secure comparison routes demonstrate
- Hardening plan — longer-term improvements beyond the immediate fix

---

## Ethical Reminder

This lab exists to teach you how vulnerabilities work so you can fix them. Every technique you practice here has a defensive purpose — you must understand attacks to design defenses.

Everything you do in this lab stays in this lab. Applying these techniques to any real system you do not own and do not have written authorization to test is illegal.

Think like an attacker. Report like a defender.
