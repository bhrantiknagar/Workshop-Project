// Toggles the responsive sidebar on smaller screens.
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.querySelector("[data-sidebar]");

    if (!toggle || !sidebar) {
        return;
    }

    toggle.addEventListener("click", () => {
        sidebar.classList.toggle("is-open");
    });
});
