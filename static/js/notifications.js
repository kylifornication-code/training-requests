/**
 * Notification and real-time update utilities for Training Request System
 */

class NotificationManager {
    constructor() {
        this.lastPendingCount = 0;
        this.updateInterval = 30000; // 30 seconds
        this.checkInterval = 60000;  // 60 seconds
        this.init();
    }

    init() {
        // Only initialize for leadership users
        if (this.isLeadershipUser()) {
            this.startPendingCountUpdates();
            this.startNewRequestChecks();
        }
    }

    isLeadershipUser() {
        // Check if user has leadership role based on navbar elements
        return document.getElementById('leadershipDropdown') !== null;
    }

    async fetchPendingCount() {
        try {
            const response = await fetch('/api/pending-count/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();
            return data.pending_count;
        } catch (error) {
            console.log('Failed to fetch pending count:', error);
            return null;
        }
    }

    updatePendingCountDisplay(count) {
        // Update navigation badge
        const navBadge = document.getElementById('navPendingBadge');
        const leadershipLink = document.getElementById('leadershipDropdown');
        
        if (count > 0) {
            if (navBadge) {
                navBadge.textContent = count;
                navBadge.style.display = 'inline';
            } else if (leadershipLink) {
                // Create badge if it doesn't exist
                const badge = document.createElement('span');
                badge.id = 'navPendingBadge';
                badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-warning text-dark';
                badge.style.fontSize = '0.6rem';
                badge.textContent = count;
                leadershipLink.appendChild(badge);
            }
        } else if (navBadge) {
            navBadge.style.display = 'none';
        }

        // Update dropdown badges
        const dropdownBadges = document.querySelectorAll('.dropdown-menu .badge');
        dropdownBadges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        });

        // Update page title for leadership pages
        if (count > 0 && this.isLeadershipPage()) {
            const currentTitle = document.title.replace(/^\(\d+\)\s/, '');
            document.title = `(${count}) ${currentTitle}`;
        } else if (count === 0) {
            document.title = document.title.replace(/^\(\d+\)\s/, '');
        }

        // Update dashboard counters
        const pendingCountElement = document.getElementById('pendingCount');
        if (pendingCountElement) {
            pendingCountElement.textContent = count;
        }
    }

    isLeadershipPage() {
        const path = window.location.pathname;
        return path.includes('/leadership/') || 
               path.includes('/pending/') || 
               path.includes('/review/');
    }

    async startPendingCountUpdates() {
        // Initial update
        const count = await this.fetchPendingCount();
        if (count !== null) {
            this.updatePendingCountDisplay(count);
            this.lastPendingCount = count;
        }

        // Regular updates
        setInterval(async () => {
            const count = await this.fetchPendingCount();
            if (count !== null) {
                this.updatePendingCountDisplay(count);
            }
        }, this.updateInterval);
    }

    async startNewRequestChecks() {
        setInterval(async () => {
            const count = await this.fetchPendingCount();
            if (count !== null && count > this.lastPendingCount) {
                const newCount = count - this.lastPendingCount;
                this.showNotification(
                    `${newCount} new training request${newCount > 1 ? 's' : ''} pending review`,
                    'info',
                    {
                        action: 'View Requests',
                        url: '/leadership/'
                    }
                );
            }
            if (count !== null) {
                this.lastPendingCount = count;
            }
        }, this.checkInterval);
    }

    showNotification(message, type = 'info', options = {}) {
        // Create notification element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
        
        let actionButton = '';
        if (options.action && options.url) {
            actionButton = `
                <div class="mt-2">
                    <a href="${options.url}" class="btn btn-sm btn-outline-${type === 'info' ? 'primary' : type}">
                        ${options.action}
                    </a>
                </div>
            `;
        }
        
        alertDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-grow-1">
                    <strong><i class="fas fa-bell me-1"></i>Notification</strong>
                    <div>${message}</div>
                    ${actionButton}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-dismiss after 8 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 8000);

        // Play notification sound (if supported)
        this.playNotificationSound();
    }

    playNotificationSound() {
        // Simple notification sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            // Ignore audio errors
        }
    }

    // Utility method for showing success messages
    showSuccess(message, options = {}) {
        this.showNotification(message, 'success', options);
    }

    // Utility method for showing error messages
    showError(message, options = {}) {
        this.showNotification(message, 'danger', options);
    }

    // Utility method for showing info messages
    showInfo(message, options = {}) {
        this.showNotification(message, 'info', options);
    }

    // Utility method for showing warning messages
    showWarning(message, options = {}) {
        this.showNotification(message, 'warning', options);
    }
}

// Initialize notification manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.notificationManager = new NotificationManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}