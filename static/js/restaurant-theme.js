// Restaurant Theme JavaScript Enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Add restaurant-themed time-based greetings
    updateTimeBasedGreeting();
    
    // Add sizzling effect to loading buttons
    addSizzleEffects();
    
    // Add kitchen sound effects (optional)
    addKitchenSounds();
    
    // Update status badges with restaurant terminology
    updateStatusBadges();
});

function updateTimeBasedGreeting() {
    const greetingElements = document.querySelectorAll('h1');
    const hour = new Date().getHours();
    
    greetingElements.forEach(element => {
        if (element.textContent.includes('Welcome back')) {
            let timeGreeting = '';
            let kitchenStatus = '';
            
            if (hour >= 5 && hour < 11) {
                timeGreeting = 'Good morning';
                kitchenStatus = 'The breakfast prep is underway! ☀️';
            } else if (hour >= 11 && hour < 14) {
                timeGreeting = 'Good afternoon';
                kitchenStatus = 'Lunch service is in full swing! 🍽️';
            } else if (hour >= 14 && hour < 17) {
                timeGreeting = 'Good afternoon';
                kitchenStatus = 'Perfect time for recipe planning! 📝';
            } else if (hour >= 17 && hour < 22) {
                timeGreeting = 'Good evening';
                kitchenStatus = 'Dinner prep time - let\'s cook! 🔥';
            } else {
                timeGreeting = 'Welcome back';
                kitchenStatus = 'The kitchen never sleeps! 🌙';
            }
            
            const username = element.textContent.match(/,\s*([^!]+)!/);
            if (username) {
                element.innerHTML = `${timeGreeting}, Chef ${username[1]}! <small class="text-muted d-block">${kitchenStatus}</small>`;
            }
        }
    });
}

function addSizzleEffects() {
    // Add sizzle effect to buttons when clicked
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Don't add effect to disabled buttons
            if (this.disabled) return;
            
            this.classList.add('loading-sizzle');
            
            // Remove effect after animation
            setTimeout(() => {
                this.classList.remove('loading-sizzle');
            }, 2000);
        });
    });
}

function addKitchenSounds() {
    // Optional: Add subtle kitchen sound effects
    // This is disabled by default but can be enabled by users
    
    const soundEnabled = localStorage.getItem('kitchenSounds') === 'true';
    
    if (soundEnabled) {
        // Add click sounds to buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                // Play a subtle click sound (would need audio files)
                // playKitchenSound('click');
            });
        });
    }
}

function updateStatusBadges() {
    // Update status badges with restaurant terminology
    const statusBadges = document.querySelectorAll('.badge');
    
    statusBadges.forEach(badge => {
        const text = badge.textContent.trim().toLowerCase();
        
        switch(text) {
            case 'pending':
                badge.innerHTML = '<i class="fas fa-clock me-1"></i>In Queue';
                badge.classList.add('status-pending');
                break;
            case 'approved':
                badge.innerHTML = '<i class="fas fa-check me-1"></i>Chef Approved';
                badge.classList.add('status-approved');
                break;
            case 'denied':
                badge.innerHTML = '<i class="fas fa-times me-1"></i>Not Today';
                badge.classList.add('status-denied');
                break;
            case 'completed':
                badge.innerHTML = '<i class="fas fa-trophy me-1"></i>Mastered';
                badge.classList.add('status-completed');
                break;
        }
    });
}

// Restaurant-themed tooltips
function initRestaurantTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            customClass: 'restaurant-tooltip'
        });
    });
}

// Add restaurant-themed loading states
function showKitchenLoading(message = 'Cooking up your request...') {
    const loadingHtml = `
        <div class="kitchen-loading text-center py-4">
            <div class="loading-sizzle mb-3">
                <i class="fas fa-utensils fa-3x text-primary"></i>
            </div>
            <p class="text-muted">${message}</p>
        </div>
    `;
    
    return loadingHtml;
}

// Export functions for use in other scripts
window.restaurantTheme = {
    updateTimeBasedGreeting,
    addSizzleEffects,
    showKitchenLoading,
    initRestaurantTooltips
};

// Add some fun Easter eggs
function addEasterEggs() {
    // Konami code for special chef mode
    let konamiCode = [];
    const konamiSequence = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65]; // Up Up Down Down Left Right Left Right B A
    
    document.addEventListener('keydown', function(e) {
        konamiCode.push(e.keyCode);
        
        if (konamiCode.length > konamiSequence.length) {
            konamiCode.shift();
        }
        
        if (konamiCode.join(',') === konamiSequence.join(',')) {
            activateChefMode();
        }
    });
}

function activateChefMode() {
    // Add special chef hat to navbar brand
    const navbarBrand = document.querySelector('.navbar-brand i');
    if (navbarBrand) {
        navbarBrand.className = 'fas fa-chef-hat me-2 chef-special';
    }
    
    // Add special message
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="fas fa-chef-hat me-2"></i>
            <strong>Chef Mode Activated!</strong> You've unlocked the secret chef powers! 👨‍🍳✨
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
    }
    
    // Add confetti effect
    if (typeof confetti !== 'undefined') {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

// Initialize Easter eggs
addEasterEggs();