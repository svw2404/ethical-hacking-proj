// Copy payload button (Mission 2)
function copyPayload() {
  const text = document.getElementById("payload")?.innerText;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector(".btn-copy");
    if (btn) {
      btn.textContent = "Copied!";
      setTimeout(() => { btn.textContent = "Copy"; }, 1500);
    }
  });
}

// Auto-scroll log terminal to bottom
const logTerminal = document.querySelector(".log-terminal");
if (logTerminal) {
  logTerminal.scrollTop = logTerminal.scrollHeight;
}
