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
    const previewModal = document.querySelector("#pdfPreviewModal");
    const previewTitle = document.querySelector("#previewTitle");
    const previewMeta = document.querySelector("#previewMeta");
    const previewContent = document.querySelector("#previewContent");
    const previewClose = document.querySelector("#previewClose");
    let uploadedPdfs = [];

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
                <button class="preview-button" type="button">Preview</button>
            `;
            row.querySelector("strong").textContent = file.filename;
            row.querySelector("small").textContent = `${file.file_size} - ${file.total_pages} pages - ${file.status}`;
            row.querySelector(".preview-button").dataset.previewId = file.id;
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
        const totalPages = files.reduce((sum, file) => sum + file.total_pages, 0);
        uploadedPdfs = files;
        // Expose uploaded PDFs to other frontend scripts (e.g., PDF Chat)
        window.uploadedPdfs = uploadedPdfs;

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

        if (selectedFiles.length > 2) {
            window.showToast("Upload up to 2 PDF files only.");
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

    function closePreview() {
        if (!previewModal) {
            return;
        }
        previewModal.classList.remove("is-open");
        previewModal.setAttribute("aria-hidden", "true");
    }

    function openPreview(pdfId) {
        const pdf = uploadedPdfs.find((item) => item.id === pdfId);
        if (!pdf || !previewModal || !previewContent) {
            return;
        }

        previewTitle.textContent = pdf.filename;
        previewMeta.textContent = `${pdf.total_pages} pages`;
        if (pdf.metadata?.title || pdf.metadata?.author) {
            previewMeta.textContent += ` - ${pdf.metadata.title || "Untitled"}${pdf.metadata.author ? ` by ${pdf.metadata.author}` : ""}`;
        }

        previewContent.innerHTML = "";
        pdf.pages.forEach((page) => {
            const section = document.createElement("section");
            section.className = "preview-page";
            section.innerHTML = "<h3></h3><pre></pre>";
            section.querySelector("h3").textContent = `Page ${page.page}`;
            section.querySelector("pre").textContent = page.text || "No extractable text found on this page.";
            previewContent.appendChild(section);
        });

        previewModal.classList.add("is-open");
        previewModal.setAttribute("aria-hidden", "false");
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
        const previewButton = event.target.closest("[data-preview-id]");
        if (previewButton) {
            openPreview(previewButton.dataset.previewId);
            return;
        }

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
        uploadedPdfs = [];
        window.uploadedPdfs = uploadedPdfs;
        emptyState?.classList.remove("is-hidden");

        if (currentPdfName) {
            currentPdfName.textContent = "No PDF selected";
        }

        window.showToast("Uploaded file removed.");
    });

    previewClose?.addEventListener("click", closePreview);
    previewModal?.addEventListener("click", (event) => {
        if (event.target === previewModal) {
            closePreview();
        }
    });
});
