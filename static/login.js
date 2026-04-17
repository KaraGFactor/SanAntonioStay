const elements = {
  username: document.getElementById("username"),
  password: document.getElementById("password"),
  loginBtn: document.getElementById("loginBtn"),
  loginStatus: document.getElementById("loginStatus"),
};

function updateStatus(message) {
  elements.loginStatus.textContent = message;
}

async function submitLogin() {
  const response = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: elements.username.value.trim(),
      password: elements.password.value,
    }),
  });

  if (!response.ok) {
    const payload = await response.json();
    updateStatus(payload.error || "Sign-in failed.");
    return;
  }

  window.location.href = "/admin.html";
}

elements.loginBtn.addEventListener("click", submitLogin);
elements.password.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    submitLogin();
  }
});
