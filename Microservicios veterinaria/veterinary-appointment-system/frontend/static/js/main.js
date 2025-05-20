// Main JavaScript file for the veterinary appointment system

// DOM loaded event listener
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if any
    initializeTooltips();

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Form validation
    initializeFormValidation();

    // Mobile menu toggle
    initializeMobileMenu();
});

// Initialize tooltips
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.classList.add('tooltip');
        const tooltipText = document.createElement('span');
        tooltipText.className = 'tooltiptext';
        tooltipText.textContent = element.getAttribute('data-tooltip');
        element.appendChild(tooltipText);
    });
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });

    // Real-time validation
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

// Validate individual field
function validateField(field) {
    let isValid = true;
    const value = field.value.trim();

    // Check if required
    if (field.hasAttribute('required') && !value) {
        isValid = false;
    }

    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
        }
    }

    // Password length validation
    if (field.type === 'password' && value) {
        if (value.length < 6) {
            isValid = false;
        }
    }

    // Phone validation
    if (field.type === 'tel' && value) {
        const phoneRegex = /^[\d\s\-\+\(\)]+$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
        }
    }

    // Update field styling
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
}

// Initialize mobile menu
function initializeMobileMenu() {
    // Create mobile menu button if needed
    const navbar = document.querySelector('.navbar');
    if (navbar && window.innerWidth <= 768) {
        const menuButton = document.createElement('button');
        menuButton.className = 'mobile-menu-button';
        menuButton.innerHTML = '☰';
        menuButton.addEventListener('click', toggleMobileMenu);

        const container = navbar.querySelector('.container');
        if (container) {
            container.appendChild(menuButton);
        }
    }
}

// Toggle mobile menu
function toggleMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
        navLinks.classList.toggle('active');
    }
}

// API helper functions
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API fetch error:', error);
        throw error;
    }
}

// Update available time slots (used in appointment form)
async function updateAvailableSlots() {
    const veterinarianId = document.getElementById('veterinarian_id').value;
    const appointmentDate = document.getElementById('appointment_date').value;
    const timeSelect = document.getElementById('appointment_time');

    if (!veterinarianId || !appointmentDate) {
        timeSelect.innerHTML = '<option value="">Seleccione primero veterinario y fecha</option>';
        return;
    }

    // Show loading state
    timeSelect.innerHTML = '<option value="">Cargando horarios...</option>';
    timeSelect.disabled = true;

    try {
        const response = await fetchAPI(`/api/appointments/available-slots/${veterinarianId}?date=${appointmentDate}`);

        timeSelect.innerHTML = '<option value="">Seleccione una hora...</option>';

        if (response.available_slots && response.available_slots.length > 0) {
            response.available_slots.forEach(slot => {
                const option = document.createElement('option');
                option.value = slot;
                option.textContent = slot;
                timeSelect.appendChild(option);
            });
        } else {
            timeSelect.innerHTML = '<option value="">No hay horarios disponibles</option>';
        }
    } catch (error) {
        console.error('Error loading available slots:', error);
        timeSelect.innerHTML = '<option value="">Error al cargar horarios</option>';
    } finally {
        timeSelect.disabled = false;
    }
}

// Add pet modal functions
function showAddPetModal() {
    const modal = document.getElementById('add-pet-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeAddPetModal() {
    const modal = document.getElementById('add-pet-modal');
    if (modal) {
        modal.style.display = 'none';
        const form = document.getElementById('add-pet-form');
        if (form) {
            form.reset();
        }
    }
}

// Add pet function
async function addPet() {
    const form = document.getElementById('add-pet-form');
    if (!form) return;

    // Get user data from window object (set by template)
    const userData = window.veterinaryUserData;
    if (!userData || !userData.authToken) {
        alert('Sesión no válida. Por favor recarga la página.');
        return;
    }

    const petData = {
        owner_id: userData.userId,
        name: form.pet_name.value,
        species: form.pet_species.value,
        breed: form.pet_breed.value || '',
        age: parseInt(form.pet_age.value) || null,
        weight: parseFloat(form.pet_weight.value) || null
    };

    // Validate required fields
    if (!petData.name || !petData.species) {
        alert('Por favor complete todos los campos requeridos');
        return;
    }

    try {
        // Use proxy endpoint in frontend instead of direct service call
        const response = await fetch('/api/appointments/pets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userData.authToken}`
            },
            body: JSON.stringify(petData)
        });

        if (response.ok) {
            alert('Mascota agregada exitosamente');
            closeAddPetModal();
            // Reload the page to show the new pet
            window.location.reload();
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Error al agregar mascota');
        }
    } catch (error) {
        console.error('Error adding pet:', error);
        alert('Error al agregar la mascota. Por favor intente nuevamente.');
    }
}

// Notification functions
function markNotificationAsRead(notificationId) {
    fetchAPI(`/api/notifications/${notificationId}/mark-read`, {
        method: 'PUT'
    }).then(() => {
        const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationElement) {
            notificationElement.style.opacity = '0.5';
        }
    }).catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

// Date formatting function
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    return date.toLocaleDateString('es-ES', options);
}

// Time formatting function
function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
}

// Appointment status update
async function updateAppointmentStatus(appointmentId, newStatus) {
    if (!confirm(`¿Está seguro de cambiar el estado de la cita a ${newStatus}?`)) {
        return;
    }

    try {
        const response = await fetchAPI(`/api/appointments/${appointmentId}`, {
            method: 'PUT',
            body: JSON.stringify({ status: newStatus })
        });

        if (response.success) {
            alert('Estado actualizado exitosamente');
            window.location.reload();
        }
    } catch (error) {
        console.error('Error updating appointment status:', error);
        alert('Error al actualizar el estado de la cita');
    }
}

// Search functionality
function setupSearch() {
    const searchInput = document.getElementById('search-appointments');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            filterAppointments(searchTerm);
        }, 300));
    }
}

// Filter appointments based on search term
function filterAppointments(searchTerm) {
    const appointmentCards = document.querySelectorAll('.appointment-card');
    appointmentCards.forEach(card => {
        const textContent = card.textContent.toLowerCase();
        if (textContent.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export data functionality
function exportAppointments() {
    // This is a placeholder for export functionality
    alert('Función de exportación en desarrollo');
}

// Print appointments
function printAppointments() {
    window.print();
}

// Initialize charts for dashboard statistics (if using Chart.js)
function initializeCharts() {
    const statsChart = document.getElementById('stats-chart');
    if (statsChart && typeof Chart !== 'undefined') {
        new Chart(statsChart, {
            type: 'bar',
            data: {
                labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'],
                datasets: [{
                    label: 'Citas por día',
                    data: [12, 19, 3, 5, 2],
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    borderColor: 'rgba(76, 175, 80, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Logout confirmation
function confirmLogout() {
    if (confirm('¿Está seguro de que desea cerrar sesión?')) {
        window.location.href = '/logout';
    }
}

// Pet species icons
const petIcons = {
    'Perro': '🐕',
    'Gato': '🐈',
    'Ave': '🐦',
    'Conejo': '🐰',
    'Pez': '🐠',
    'Otro': '🐾'
};

// Get pet icon based on species
function getPetIcon(species) {
    return petIcons[species] || petIcons['Otro'];
}

// Initialize calendar view (if implemented)
function initializeCalendarView() {
    const calendarElement = document.getElementById('appointment-calendar');
    if (calendarElement) {
        // Calendar implementation would go here
        console.log('Calendar view initialized');
    }
}

// Responsive table handling
function handleResponsiveTables() {
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
});

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupSearch();
    handleResponsiveTables();
    initializeCharts();
    initializeCalendarView();
});

// Service worker registration (for PWA functionality)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
        }, function(err) {
            console.log('ServiceWorker registration failed:', err);
        });
    });
}

// Notification permission request
function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        });
    }
}

// Show browser notification
function showBrowserNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: body,
            icon: '/static/img/logo.png'
        });
    }
}

// Copy to clipboard function
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    alert('Copiado al portapapeles');
}

// Export all public functions for use in templates
window.veterinaryApp = {
    updateAvailableSlots,
    showAddPetModal,
    closeAddPetModal,
    addPet,
    markNotificationAsRead,
    updateAppointmentStatus,
    exportAppointments,
    printAppointments,
    confirmLogout,
    requestNotificationPermission,
    showBrowserNotification,
    copyToClipboard,
    formatDate,
    formatTime,
    getPetIcon
};