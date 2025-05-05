/**
 * Main JavaScript file for the MultiAgent System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Handle file uploads
    setupFileUploads();
    
    // Setup project creation
    setupProjectCreation();
    
    // Check if Ollama is running
    checkOllamaStatus();
});

/**
 * Setup file upload functionality
 */
function setupFileUploads() {
    const fileInputs = document.querySelectorAll('.custom-file-input');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            // Update the file label
            const fileName = this.files[0]?.name || 'No file chosen';
            const fileLabel = this.nextElementSibling;
            if (fileLabel) {
                fileLabel.textContent = fileName;
            }
            
            // If this is an image upload for chat, show the preview
            if (this.id === 'imageUpload' && this.files[0]) {
                const imagePreviewContainer = document.getElementById('imagePreviewContainer');
                const imagePreview = document.getElementById('imagePreview');
                
                if (imagePreviewContainer && imagePreview) {
                    const file = this.files[0];
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        imagePreview.src = e.target.result;
                        imagePreviewContainer.classList.remove('d-none');
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    });
    
    // Clear image preview when button is clicked
    const clearImageButton = document.getElementById('clearImage');
    if (clearImageButton) {
        clearImageButton.addEventListener('click', function() {
            const imageInput = document.getElementById('imageUpload');
            const imagePreviewContainer = document.getElementById('imagePreviewContainer');
            const imagePreview = document.getElementById('imagePreview');
            const fileLabel = document.querySelector('label[for="imageUpload"]');
            
            if (imageInput) {
                imageInput.value = '';
            }
            
            if (fileLabel) {
                fileLabel.textContent = 'Choose image...';
            }
            
            if (imagePreviewContainer && imagePreview) {
                imagePreview.src = '';
                imagePreviewContainer.classList.add('d-none');
            }
        });
    }
}

/**
 * Setup project creation functionality
 */
function setupProjectCreation() {
    const createProjectForm = document.getElementById('createProjectForm');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const projectName = document.getElementById('projectName').value;
            const projectDescription = document.getElementById('projectDescription').value;
            
            if (!projectName) {
                showAlert('Please enter a project name', 'danger');
                return;
            }
            
            // Send project creation request
            fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: projectName,
                    description: projectDescription
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error creating project');
                }
                return response.json();
            })
            .then(data => {
                showAlert('Project created successfully!', 'success');
                
                // Redirect to the project page
                window.location.href = `/project/${data.id}`;
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Failed to create project: ' + error.message, 'danger');
            });
        });
    }
}

/**
 * Check if Ollama is running and display status
 */
function checkOllamaStatus() {
    const statusElement = document.getElementById('ollamaStatus');
    if (!statusElement) return;
    
    fetch('/api/ollama/status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                statusElement.innerHTML = '<span class="badge bg-success">Ollama Running</span>';
            } else {
                statusElement.innerHTML = '<span class="badge bg-danger">Ollama Not Running</span>';
            }
        })
        .catch(error => {
            console.error('Error checking Ollama status:', error);
            statusElement.innerHTML = '<span class="badge bg-warning">Status Unknown</span>';
        });
}

/**
 * Display an alert message
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, info, warning, danger)
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alertElement);
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(alertElement);
        alert.close();
    }, 5000);
}
