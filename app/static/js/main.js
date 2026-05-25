// Copy button for Mission 2 transmissions
function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText;
  navigator.clipboard.writeText(text).then(() => {
    // Find the button that triggered the copy (sibling of element's parent)
    const btn = el.parentElement?.querySelector(".btn-copy");
    if (btn) {
      const original = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => { btn.textContent = original; }, 1500);
    }
  });
}

// Backwards-compat alias used in older templates
function copyPayload() { copyText("payload"); }

// Auto-scroll log terminal to bottom
const logTerminal = document.querySelector(".log-terminal");
if (logTerminal) {
  logTerminal.scrollTop = logTerminal.scrollHeight;
}
