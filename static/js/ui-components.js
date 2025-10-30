/**
 * UI Components JavaScript
 * Common functionality for Training Request System UI components
 */

class UIComponents {
    constructor() {
        this.init();
    }

    init() {
        this.initTooltips();
        this.initConfirmModals();
        this.initFilterForms();
        this.initLoadingStates();
        this.initFormValidation();
    }

    // Initialize Bootstrap tooltips
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize confirmation modals
    initConfirmModals() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-confirm]')) {
                e.preventDefault();
                const element = e.target;
                const message = element.dataset.confirm;
                const action = element.href || element.dataset.action;
                
                this.showConfirmModal(message, action);
            }
        });
    }

    // Show confirmation modal
    showConfirmModal(message, action) {
        const modalHtml = `
            <div class="modal fade" id="dynamicConfirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle me-2"></i>Confirm Action
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmAction">
                                <i class="fas fa-check me-1"></i>Confirm
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if present
        const existingModal = document.getElementById('dynamicConfirmModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('dynamicConfirmModal'));
        
        // Handle confirm action
        document.getElementById('confirmAction').addEventListener('click', () => {
            if (action.startsWith('http')) {
                window.location.href = action;
            } else {
                // Handle form submission or other actions
                eval(action);
            }
            modal.hide();
        });

        // Clean up modal after hiding
        document.getElementById('dynamicConfirmModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('dynamicConfirmModal').remove();
        });

        modal.show();
    }

    // Initialize filter forms with auto-submit
    initFilterForms() {
        const filterForms = document.querySelectorAll('[data-auto-submit]');
        filterForms.forEach(form => {
            const selects = form.querySelectorAll('select');
            selects.forEach(select => {
                select.addEventListener('change', () => {
                    form.submit();
                });
            });
        });
    }

    // Initialize loading states for buttons
    initLoadingStates() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-loading]')) {
                const button = e.target;
                const originalText = button.innerHTML;
                const loadingText = button.dataset.loading || 'Loading...';
                
                button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${loadingText}`;
                button.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 5000);
            }
        });
    }

    // Initialize form validation
    initFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }

    // Show toast notification
    showToast(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1055';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Animate counter
    animateCounter(element, target, duration = 1000) {
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }

    // Format currency
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    // Format date
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
    }
}

// Initialize UI components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.uiComponents = new UIComponents();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIComponents;
}