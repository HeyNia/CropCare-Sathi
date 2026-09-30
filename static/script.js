document.addEventListener("DOMContentLoaded", () => {
    const imageInput = document.getElementById("image");
    const fileDropzone = document.getElementById("file-dropzone");
    const selectedFile = document.getElementById("selected-file");
    const imagePreview = document.getElementById("image-preview");
    const diagnosisForm = document.getElementById("diagnosis-form");
    const submitButton = document.getElementById("submit-button");
    const uiLanguageInput = document.getElementById("ui_lang");

    if (uiLanguageInput) {
        const browserLanguage = navigator.language || "en";
        uiLanguageInput.value = browserLanguage.split("-")[0].toLowerCase();
    }

    const formatFileSize = (bytes) => {
        if (!bytes) {
            return "0 Bytes";
        }

        const units = ["Bytes", "KB", "MB", "GB"];
        const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024));
        const size = bytes / Math.pow(1024, unitIndex);

        return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
    };

    const resetPreview = () => {
        if (imagePreview) {
            imagePreview.src = "";
            imagePreview.hidden = true;
        }

        if (selectedFile) {
            selectedFile.textContent = "No file selected";
        }
    };

    const showSelectedFile = (file) => {
        if (!file) {
            resetPreview();
            return;
        }

        const supportedTypes = ["image/png", "image/jpeg", "image/webp"];
        const maxSize = 8 * 1024 * 1024;

        if (!supportedTypes.includes(file.type)) {
            alert("Please select a PNG, JPG, JPEG, or WEBP image.");
            imageInput.value = "";
            resetPreview();
            return;
        }

        if (file.size > maxSize) {
            alert("This image is larger than 8 MB. Please choose a smaller file.");
            imageInput.value = "";
            resetPreview();
            return;
        }

        if (selectedFile) {
            selectedFile.textContent = `${file.name} (${formatFileSize(file.size)})`;
        }

        if (imagePreview) {
            const reader = new FileReader();

            reader.onload = (event) => {
                imagePreview.src = event.target.result;
                imagePreview.hidden = false;
            };

            reader.readAsDataURL(file);
        }
    };

    if (imageInput) {
        imageInput.addEventListener("change", () => {
            showSelectedFile(imageInput.files[0]);
        });
    }

    if (fileDropzone && imageInput) {
        ["dragenter", "dragover"].forEach((eventName) => {
            fileDropzone.addEventListener(eventName, (event) => {
                event.preventDefault();
                fileDropzone.classList.add("drag-active");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            fileDropzone.addEventListener(eventName, (event) => {
                event.preventDefault();
                fileDropzone.classList.remove("drag-active");
            });
        });

        fileDropzone.addEventListener("drop", (event) => {
            const droppedFiles = event.dataTransfer.files;

            if (!droppedFiles || droppedFiles.length === 0) {
                return;
            }

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(droppedFiles[0]);
            imageInput.files = dataTransfer.files;

            showSelectedFile(droppedFiles[0]);
        });
    }

    if (diagnosisForm && submitButton && imageInput) {
        diagnosisForm.addEventListener("submit", (event) => {
            if (!imageInput.files || imageInput.files.length === 0) {
                event.preventDefault();
                alert("Please choose a crop or plant image first.");
                return;
            }

            submitButton.disabled = true;
            submitButton.innerHTML = `
                <span>Analyzing image...</span>
                <span aria-hidden="true">⌛</span>
            `;
        });
    }
});