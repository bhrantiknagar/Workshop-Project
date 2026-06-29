// Handles placeholder chat interactions until the AI pipeline is connected.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#chatForm");
    const input = document.querySelector("#questionInput");
    const messages = document.querySelector("#messages");

    if (!form || !input || !messages) {
        return;
    }

    function addMessage(text, type) {
        const row = document.createElement("div");
        row.className = `message ${type}-message`;
        row.innerHTML = `<span class="avatar">${type === "user" ? "You" : "AI"}</span><p></p>`;
        row.querySelector("p").textContent = text;
        messages.appendChild(row);
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const question = input.value.trim();

        if (!question) {
            return;
        }

        addMessage(question, "user");
        input.value = "";

        const response = await fetch("/chat/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question }),
        });
        const data = await response.json();
        addMessage(data.answer, "assistant");
    });
});
