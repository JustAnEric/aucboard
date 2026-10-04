async function handleLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const btn = document.getElementById('loginBtn');
    const msg = document.getElementById('message');

    btn.classList.add('loading');
    btn.disabled = true;
    msg.innerText = "";
    try {
        const response = await fetch(`/login`, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        const data = await response.json();

        if (response.ok) {
            msg.style.color = "#00ffcc";
            msg.innerText = "welcome back!";
            setTimeout(() => window.location = "/dashboard", 1*1000);
        } else {
            msg.style.color = "#ff5555";
            msg.innerText = "invalid credentials...";
        }
    } catch (error) {
        msg.style.color = "#ffc800";
        msg.innerText = "hardware offline?";
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('loginBtn');
    btn.addEventListener('click', async () => await handleLogin());
});