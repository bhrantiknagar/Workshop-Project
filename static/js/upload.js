// Handles PDF upload requests from the dashboard.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#uploadForm");
    const status = document.querySelector("#uploadStatus");
    const fileInput = document.querySelector("#pdfFile");

    if (!form || !status || !fileInput) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!fileInput.files.length) {
            status.textContent = "Choose a PDF before uploading.";
            return;
        }

        const formData = new FormData(form);
        status.textContent = "Uploading document...";

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            status.textContent = data.message;
        } catch (error) {
            status.textContent = "Upload failed. Check the Flask server logs.";
        }
    });
});
