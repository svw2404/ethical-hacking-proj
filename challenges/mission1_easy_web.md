# Mission 1 — Staff Portal Leak

## Challenge Creator Form

| Field       | Value |
|-------------|-------|
| **Name**    | Staff Portal Leak |
| **Category**| Web / Information Disclosure |
| **Difficulty** | Easy |
| **Points**  | 100 |
| **Route**   | `/mission1` |

### Story / Description

The Red Team discovers an internal staff portal belonging to Atlas Core Systems.
The page looks like a normal employee access gateway — a login form, an icon, standard corporate branding.

However, a developer accidentally left sensitive debugging information inside the page's source code before pushing to production. The rendered page looks completely clean; the secret is invisible to the naked eye.

**Your mission:** Inspect the page source and recover the first flag.

### Hints

1. Have you tried looking at what the browser receives but does not display on screen?
2. Right-click on the page and select "View Page Source." Look for HTML comment tags `<!-- -->`.
3. Search the page source for the keyword `flag` or `picoCTF`.

### Flag

```
picoCTF{html_comments_are_dangerous}
```

---

## Challenge Solver Report

### Initial Analysis

The page shows a standard login form with username and password fields. Entering random credentials returns no feedback (the form redirects without success). The challenge hint says "developers sometimes leave clues behind," which is a strong signal to check the page source.

### Tools Used

- Google Chrome or Firefox browser
- View Page Source (Ctrl+U / Cmd+U)
- Browser DevTools (F12 → Elements tab)

### Exploitation Steps

1. Open the staff portal at `/mission1`.
2. Press `Ctrl+U` (or right-click → View Page Source).
3. Search the source code for `picoCTF` using `Ctrl+F`.
4. Locate the HTML comment block near the top of the `<body>`:

```html
<!--
  DEBUG NOTE: Temporary login disabled for maintenance.
  Use flag for emergency bypass: picoCTF{html_comments_are_dangerous}
-->
```

5. Copy the flag string.

### Flag Found

```
picoCTF{html_comments_are_dangerous}
```

### Learning Points

- HTML comments are delivered to every browser that loads the page. They are not hidden from users — only invisible in the rendered view.
- Developers frequently leave debugging notes, credentials, flags, and internal comments in source code. These must be removed before deployment.
- This vulnerability is classified under **OWASP A05:2021 — Security Misconfiguration** and **Sensitive Data Exposure**.
- The mitigation is simple: never place secret data in client-side code. Store secrets server-side in environment variables or a secrets manager.

---

## Blue Team — Vulnerability Explanation

### Root Cause

Sensitive debugging information was placed inside an HTML comment in the production page source code. The developer likely added it during testing and forgot to remove it before deployment.

### Security Impact

- Any user can view the full HTML source of any web page by pressing `Ctrl+U` or using browser DevTools.
- HTML comments, embedded JavaScript values, hidden form fields, and inline CSS can all expose sensitive information.
- Real-world examples include API keys, admin passwords, database connection strings, and internal debug endpoints found in HTML comments.

### Mitigation Strategy

| Control | Description |
|---------|-------------|
| Code review | Review all HTML/JS before deployment; search for comment tags |
| Deployment checklist | Add a "remove debug comments" step to the CI/CD pipeline |
| Secret storage | Store all sensitive values in environment variables or a vault |
| DevTools testing | Before going live, inspect your own page source as an attacker would |

### OWASP Reference

- **A05:2021 — Security Misconfiguration**
- **A02:2021 — Cryptographic Failures** (storing secrets client-side)
