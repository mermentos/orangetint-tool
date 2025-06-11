// SORA Image Tint Corrector - Client-side functionality

document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const fileItems = document.getElementById('fileItems');
    const processBtn = document.getElementById('processBtn');
    const clearFilesBtn = document.getElementById('clearFiles');
    const uploadForm = document.getElementById('uploadForm');
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    let selectedFiles = new Map();

    // Drag and drop functionality
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    });

    // Click to select files
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', function() {
        const files = Array.from(this.files);
        handleFiles(files);
    });

    // Clear files button
    if (clearFilesBtn) {
        clearFilesBtn.addEventListener('click', function() {
            selectedFiles.clear();
            updateFileList();
            updateProcessButton();
        });
    }

    // Form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (selectedFiles.size === 0) {
                showAlert('Please select at least one image to process.', 'error');
                return;
            }

            // Create FormData with selected files
            const formData = new FormData();
            selectedFiles.forEach((file) => {
                formData.append('files', file);
            });

            // Show progress
            showProgress();
            
            // Submit form
            fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    return response.text();
                }
            })
            .then(html => {
                if (html) {
                    document.body.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                hideProgress();
                showAlert('An error occurred while processing your images.', 'error');
            });
        });
    }

    function handleFiles(files) {
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
        const maxSize = 16 * 1024 * 1024; // 16MB
        
        files.forEach(file => {
            // Check file type
            if (!allowedTypes.includes(file.type)) {
                showAlert(`Invalid file type: ${file.name}. Please select PNG, JPG, JPEG, or WEBP files.`, 'error');
                return;
            }
            
            // Check file size
            if (file.size > maxSize) {
                showAlert(`File too large: ${file.name}. Maximum size is 16MB.`, 'error');
                return;
            }
            
            // Add to selected files
            selectedFiles.set(file.name, file);
        });
        
        updateFileList();
        updateProcessButton();
    }

    function updateFileList() {
        if (selectedFiles.size === 0) {
            fileList.style.display = 'none';
            return;
        }

        fileList.style.display = 'block';
        fileItems.innerHTML = '';

        selectedFiles.forEach((file, filename) => {
            const fileItem = createFileItem(file, filename);
            fileItems.appendChild(fileItem);
        });
    }

    function createFileItem(file, filename) {
        const item = document.createElement('div');
        item.className = 'list-group-item file-item d-flex justify-content-between align-items-center';
        
        const fileInfo = document.createElement('div');
        fileInfo.className = 'd-flex align-items-center';
        
        const icon = document.createElement('div');
        icon.className = 'file-icon me-3';
        icon.textContent = getFileExtension(filename).toUpperCase();
        
        const details = document.createElement('div');
        details.innerHTML = `
            <div class="fw-medium">${filename}</div>
            <div class="file-size">${formatFileSize(file.size)}</div>
        `;
        
        fileInfo.appendChild(icon);
        fileInfo.appendChild(details);
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-outline-danger btn-sm';
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.onclick = () => {
            selectedFiles.delete(filename);
            updateFileList();
            updateProcessButton();
        };
        
        item.appendChild(fileInfo);
        item.appendChild(removeBtn);
        
        return item;
    }

    function updateProcessButton() {
        if (processBtn) {
            processBtn.disabled = selectedFiles.size === 0;
            
            if (selectedFiles.size > 0) {
                processBtn.innerHTML = `
                    <i class="fas fa-magic me-2"></i>
                    Process ${selectedFiles.size} Image${selectedFiles.size > 1 ? 's' : ''}
                `;
            } else {
                processBtn.innerHTML = `
                    <i class="fas fa-magic me-2"></i>
                    Process Images
                `;
            }
        }
    }

    function showProgress() {
        if (progressSection) {
            progressSection.style.display = 'block';
            processBtn.disabled = true;
            
            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 20;
                if (progress > 90) {
                    progress = 90;
                    clearInterval(interval);
                }
                
                progressBar.style.width = progress + '%';
                progressText.textContent = `Processing images... ${Math.round(progress)}%`;
            }, 500);
        }
    }

    function hideProgress() {
        if (progressSection) {
            progressSection.style.display = 'none';
            processBtn.disabled = false;
        }
    }

    function showAlert(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alert.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.container');
        const firstChild = container.firstElementChild;
        container.insertBefore(alert, firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    function getFileExtension(filename) {
        return filename.split('.').pop() || '';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Initialize
    updateProcessButton();
});

// Additional utility functions
function downloadAll() {
    const downloadLinks = document.querySelectorAll('a[href*="download"]');
    downloadLinks.forEach((link, index) => {
        setTimeout(() => {
            link.click();
        }, index * 1000); // Stagger downloads by 1 second
    });
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
});
