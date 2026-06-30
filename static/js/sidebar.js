// Toggles and highlights the dashboard sidebar.
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.querySelector("[data-sidebar]");
    const links = document.querySelectorAll(".sidebar-link");

    if (toggle && sidebar) {
        toggle.addEventListener("click", () => {
            sidebar.classList.toggle("is-open");
        });
    }

    links.forEach((link) => {
        link.addEventListener("click", () => {
            links.forEach((item) => item.classList.remove("active"));
            link.classList.add("active");

            if (sidebar) {
                sidebar.classList.remove("is-open");
            }
        });
    });
});
