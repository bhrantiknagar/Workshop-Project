// Simulates PDF upload, indexing, and progress states without backend calls.
document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector("#pdfFile");
    const dropZone = document.querySelector("#dropZone");
    const progress = document.querySelector("#uploadProgress");
    const progressLabel = document.querySelector("#progressLabel");
    const currentPdfName = document.querySelector("#currentPdfName");
    const infoFilename = document.querySelector("#infoFilename");
    const infoPages = document.querySelector("#infoPages");
    const infoSize = document.querySelector("#infoSize");
    const infoStatus = document.querySelector("#infoStatus");

    if (!fileInput || !dropZone || !progress) {
        return;
    }

    function formatSize(bytes) {
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    function simulateUpload(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            window.showToast("Please choose a PDF file.");
            return;
        }

        let value = 0;
        progress.style.width = "0%";
        progressLabel.textContent = "Uploading PDF...";
        infoStatus.textContent = "Uploading";
        infoStatus.classList.remove("status-ready");

        const timer = window.setInterval(() => {
            value += 12;
            progress.style.width = `${Math.min(value, 100)}%`;

            if (value >= 55) {
                progressLabel.textContent = "Indexing document preview...";
                infoStatus.textContent = "Indexing";
            }

            if (value >= 100) {
                window.clearInterval(timer);
                progressLabel.textContent = "Ready to chat";
                infoFilename.textContent = file.name;
                infoPages.textContent = String(Math.max(6, Math.round(file.size / 85000)));
                infoSize.textContent = formatSize(file.size);
                infoStatus.textContent = "Ready";
                infoStatus.classList.add("status-ready");

                if (currentPdfName) {
                    currentPdfName.textContent = file.name;
                }

                window.showToast("PDF uploaded and indexed in preview mode.");
            }
        }, 180);
    }

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            simulateUpload(fileInput.files[0]);
        }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("is-dragging");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("is-dragging");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        const file = event.dataTransfer.files[0];
        if (file) {
            simulateUpload(file);
        }
    });
});
