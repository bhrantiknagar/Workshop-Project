// Uploads up to 3 PDFs to Flask and displays saved file metadata.
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
    const emptyState = document.querySelector("#emptyState");
    const uploadedFileList = document.querySelector("#uploadedFileList");

    if (!fileInput || !dropZone || !progress) {
        return;
    }

    function renderUploadedFiles(files) {
        if (!uploadedFileList) {
            return;
        }

        uploadedFileList.innerHTML = "";
        files.forEach((file) => {
            const row = document.createElement("article");
            row.className = "prompt-file-card";
            row.innerHTML = `
                <div>
                    <i class="fa-regular fa-file-pdf"></i>
                    <div>
                        <strong></strong>
                        <small></small>
                    </div>
                </div>
            `;
            row.querySelector("strong").textContent = file.filename;
            row.querySelector("small").textContent = `${file.file_size} - ${file.pages} pages`;
            uploadedFileList.appendChild(row);
        });

        const clearButton = document.createElement("button");
        clearButton.className = "prompt-clear-button";
        clearButton.type = "button";
        clearButton.dataset.clearUpload = "true";
        clearButton.textContent = "Clear uploaded PDFs";
        uploadedFileList.appendChild(clearButton);
        uploadedFileList.hidden = false;
    }

    function setUploadState(data) {
        const files = data.files || [];
        const totalPages = files.reduce((sum, file) => sum + file.pages, 0);

        progress.style.width = "100%";
        progressLabel.textContent = "Ready";
        if (infoFilename) {
            infoFilename.textContent = files.map((file) => file.filename).join(", ");
        }
        if (infoPages) {
            infoPages.textContent = `${totalPages} pages`;
        }
        if (infoSize) {
            infoSize.textContent = `${files.length} file${files.length === 1 ? "" : "s"}`;
        }
        if (infoStatus) {
            infoStatus.textContent = "Uploaded";
            infoStatus.classList.add("status-ready");
        }

        renderUploadedFiles(files);
        emptyState?.classList.add("is-hidden");

        if (currentPdfName) {
            currentPdfName.textContent = files.length === 1 ? files[0].filename : `${files.length} PDFs selected`;
        }

        window.showToast(data.message || "PDF uploaded successfully.");
    }

    async function uploadFiles(files) {
        const selectedFiles = Array.from(files);

        if (!selectedFiles.length) {
            return;
        }

        if (selectedFiles.length > 3) {
            window.showToast("Upload up to 3 PDF files only.");
            return;
        }

        const invalidFile = selectedFiles.find((file) => !file.name.toLowerCase().endsWith(".pdf"));
        if (invalidFile) {
            window.showToast("Please choose PDF files only.");
            return;
        }

        progress.style.width = "0%";
        progressLabel.textContent = `Uploading ${selectedFiles.length} PDF${selectedFiles.length === 1 ? "" : "s"}...`;
        if (infoStatus) {
            infoStatus.textContent = "Uploading";
            infoStatus.classList.remove("status-ready");
        }
        if (uploadedFileList) {
            uploadedFileList.hidden = true;
            uploadedFileList.innerHTML = "";
        }

        const progressTimer = window.setInterval(() => {
            const currentWidth = parseInt(progress.style.width, 10) || 0;
            if (currentWidth < 88) {
                progress.style.width = `${currentWidth + 8}%`;
            }
        }, 140);

        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append("pdf", file);
        });

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Upload failed.");
            }

            setUploadState(data);
        } catch (error) {
            progress.style.width = "0%";
            progressLabel.textContent = error.message;
            if (infoStatus) {
                infoStatus.textContent = "Failed";
            }
            window.showToast(error.message);
        } finally {
            window.clearInterval(progressTimer);
        }
    }

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            uploadFiles(fileInput.files);
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
        const files = event.dataTransfer.files;
        if (files.length) {
            uploadFiles(files);
        }
    });

    uploadedFileList?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-clear-upload]");
        if (!button) {
            return;
        }

        fileInput.value = "";
        progress.style.width = "0%";
        progressLabel.textContent = "Waiting for PDF";
        if (infoFilename) {
            infoFilename.textContent = "Not uploaded";
        }
        if (infoPages) {
            infoPages.textContent = "--";
        }
        if (infoSize) {
            infoSize.textContent = "--";
        }
        if (infoStatus) {
            infoStatus.textContent = "Idle";
        }
        uploadedFileList.hidden = true;
        uploadedFileList.innerHTML = "";
        emptyState?.classList.remove("is-hidden");

        if (currentPdfName) {
            currentPdfName.textContent = "No PDF selected";
        }

        window.showToast("Uploaded file removed.");
    });
});
