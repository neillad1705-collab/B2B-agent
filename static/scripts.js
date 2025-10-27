const chatBox = document.getElementById("chatBox");
const input = document.getElementById("userInput");

let sessionId = null; // Keep session across messages

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message: text,
      session_id: sessionId // send session if available
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.session_id) sessionId = data.session_id;
      if (data.response) {
        addMessage(data.response, "bot");
      } else if (data.error) {
        addMessage("❌ " + data.error, "bot");
      }
    })
    .catch(err => {
      addMessage("⚠️ Error: " + err.message, "bot");
    });
}

function addMessage(message, sender) {
  const messageEl = document.createElement("div");
  messageEl.className = sender;
  messageEl.innerHTML = message;
  chatBox.appendChild(messageEl);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Send message on Enter
input.addEventListener("keydown", function (e) {
  if (e.key === "Enter") sendMessage();
});
