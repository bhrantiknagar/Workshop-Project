// Requests a placeholder document summary from the Flask backend.
document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("#summaryButton");
    const output = document.querySelector("#summaryOutput");

    if (!button || !output) {
        return;
    }

    button.addEventListener("click", async () => {
        output.textContent = "Preparing summary...";
        const response = await fetch("/summary/generate", { method: "POST" });
        const data = await response.json();
        output.textContent = data.summary;
    });
});
