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
        window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
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

    if (themeToggle) {
        themeToggle.addEventListener("change", () => {
            document.body.classList.toggle("light-theme", !themeToggle.checked);
            window.showToast(themeToggle.checked ? "Dark theme enabled" : "Light preview enabled");
        });
    }
});
