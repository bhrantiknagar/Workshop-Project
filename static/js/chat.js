// Creates a frontend-only AI chat preview with typing, copy, and history.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#chatForm");
    const input = document.querySelector("#questionInput");
    const messages = document.querySelector("#messages");
    const historyList = document.querySelector("#historyList");
    const clearHistory = document.querySelector("#clearHistory");

    if (!form || !input || !messages) {
        return;
    }

    const dummyAnswers = [
        "This section appears to describe the main objective, supporting evidence, and expected outcome. Once backend AI is connected, this answer will be grounded in the uploaded PDF.",
        "A concise summary would include the problem statement, the proposed approach, and the metrics used to evaluate success.",
        "The most relevant detail is likely in the methodology or findings section. The final AI version can cite exact pages from retrieved chunks.",
    ];

    function scrollChat() {
        messages.scrollTop = messages.scrollHeight;
    }

    function createMessage(text, type, page) {
        const row = document.createElement("div");
        row.className = `message ${type}-message`;
        row.innerHTML = `
            <span class="avatar">${type === "user" ? "You" : '<i class="fa-solid fa-wand-magic-sparkles"></i>'}</span>
            <div class="message-content">
                <p></p>
                <div class="message-actions">
                    <button type="button" class="copy-button">
                        <i class="fa-regular fa-copy"></i>
                        Copy
                    </button>
                    <span class="page-badge">Page ${page}</span>
                </div>
            </div>
        `;
        row.querySelector("p").textContent = text;
        row.querySelector(".copy-button").dataset.copy = text;
        messages.appendChild(row);
        scrollChat();
    }

    function addTyping() {
        const row = document.createElement("div");
        row.className = "message ai-message typing-row";
        row.innerHTML = `
            <span class="avatar"><i class="fa-solid fa-wand-magic-sparkles"></i></span>
            <div class="typing"><span></span><span></span><span></span></div>
        `;
        messages.appendChild(row);
        scrollChat();
        return row;
    }

    function addHistory(question) {
        if (!historyList) {
            return;
        }

        const empty = historyList.querySelector(".empty-state");
        if (empty) {
            empty.remove();
        }

        const item = document.createElement("div");
        item.className = "history-item";
        item.innerHTML = `
            <div>
                <strong></strong>
                <small>Just now</small>
            </div>
            <button class="delete-history" type="button" aria-label="Delete question">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
        item.querySelector("strong").textContent = question;
        historyList.prepend(item);
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const question = input.value.trim();

        if (!question) {
            window.showToast("Type a question first.");
            return;
        }

        createMessage(question, "user", "--");
        addHistory(question);
        input.value = "";

        const typing = addTyping();
        window.setTimeout(() => {
            typing.remove();
            const answer = dummyAnswers[Math.floor(Math.random() * dummyAnswers.length)];
            createMessage(answer, "ai", Math.floor(Math.random() * 24) + 1);
        }, 950);
    });

    messages.addEventListener("click", (event) => {
        const button = event.target.closest(".copy-button");
        if (!button) {
            return;
        }

        navigator.clipboard?.writeText(button.dataset.copy || "");
        window.showToast("Copied message.");
    });

    historyList?.addEventListener("click", (event) => {
        const button = event.target.closest(".delete-history");
        if (button) {
            button.closest(".history-item").remove();
            window.showToast("History item deleted.");
        }
    });

    clearHistory?.addEventListener("click", () => {
        if (historyList) {
            historyList.innerHTML = `
                <div class="history-item empty-state">
                    <i class="fa-regular fa-message"></i>
                    <span>No questions yet</span>
                    <small>Ask something about your PDF to build history.</small>
                </div>
            `;
        }
        window.showToast("History cleared.");
    });
});
