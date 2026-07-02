// Shared UI helpers for SmartPDF AI.
document.addEventListener("DOMContentLoaded", () => {
    const toast = document.querySelector("#toast");
    const themeToggle = document.querySelector("#themeToggle");
    const modalButtons = document.querySelectorAll("[data-modal-open]");
    const closeButtons = document.querySelectorAll("[data-modal-close]");

    document.body.classList.add("is-ready");

    window.showToast = (message) => {
        if (!toast) {
            return;
        }

        toast.textContent = message;
        toast.classList.add("is-visible");
        window.setTimeout(() => toast.classList.remove("is-visible"), 3000);
    };

    modalButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const modal = document.querySelector(`#${button.dataset.modalOpen}`);
            if (modal) {
                modal.classList.add("is-open");
                modal.setAttribute("aria-hidden", "false");
            }
        });
    });

    closeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const modal = button.closest(".modal-backdrop");
            if (modal) {
                modal.classList.remove("is-open");
                modal.setAttribute("aria-hidden", "true");
            }
        });
    });

    document.querySelectorAll(".modal-backdrop").forEach((modal) => {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                modal.classList.remove("is-open");
                modal.setAttribute("aria-hidden", "true");
            }
        });
    });

    const llmPrompt = document.querySelector("#llmPrompt");
    const llmGenerateButton = document.querySelector("#llmGenerateButton");
    const llmStatus = document.querySelector("#llmStatus");
    const llmResponse = document.querySelector("#llmResponse");

    if (llmGenerateButton && llmPrompt && llmStatus && llmResponse) {
        llmGenerateButton.addEventListener("click", async () => {
            const prompt = llmPrompt.value.trim();
            if (!prompt) {
                llmResponse.textContent = "Please enter a prompt first.";
                llmStatus.textContent = "Empty prompt";
                return;
            }

            llmStatus.textContent = "Generating...";
            llmResponse.textContent = "";

            try {
                const response = await fetch("/api/test-llm", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ prompt }),
                });
                const payload = await response.json();

                if (!response.ok) {
                    throw new Error(payload.error || "LLM request failed.");
                }

                llmResponse.textContent = payload.response || "No response received.";
                llmStatus.textContent = "Ready";
            } catch (error) {
                llmResponse.textContent = error.message;
                llmStatus.textContent = "Error";
            }
        });
    }

    if (themeToggle) {
        themeToggle.addEventListener("change", () => {
            const mode = themeToggle.value;
            document.body.classList.toggle("light-theme", mode === "light");
            window.showToast(`${mode.charAt(0).toUpperCase() + mode.slice(1)} theme selected`);
        });
    }
});
