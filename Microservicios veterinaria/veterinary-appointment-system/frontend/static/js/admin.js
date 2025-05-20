// admin.js - Funcionalidades para el panel de administrador

// Variables globales
let staffList = [];
let clientsList = [];
let currentStaffSchedules = {};
let currentClientId = null;
let systemSettings = {};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setupEventListeners();
});

// Función para cambiar entre pestañas
function switchTab(tabName) {
    // Ocultar todas las pestañas
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.style.display = 'none';
    });

    // Desactivar todos los enlaces de navegación
    document.querySelectorAll('.admin-nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Mostrar la pestaña seleccionada
    document.getElementById(`admin-${tabName}-tab`).style.display = 'block';

    // Activar el enlace de navegación correspondiente
    document.querySelector(`.admin-nav-link[onclick*="${tabName}"]`).classList.add('active');

    // Cargar datos específicos según la pestaña
    if (tabName === 'dashboard') {
        loadDashboardData();
    } else if (tabName === 'staff') {
        loadStaffList();
    } else if (tabName === 'clients') {
        loadClientsList();
        loadClientsStats();
    } else if (tabName === 'schedules') {
        loadStaffForSchedules();
    } else if (tabName === 'settings') {
        loadSystemSettings();
    }
}

// ===== DASHBOARD =====

// Cargar datos del dashboard
function loadDashboardData() {
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`
    };

    // Cargar estadísticas de personal
    fetch('/api/admin/dashboard/stats', { headers })
        .then(response => response.json())
        .then(data => {
            if (data.staff_stats) {
                document.getElementById('vets-count').textContent = data.staff_stats.veterinarians;
                document.getElementById('receptionists-count').textContent = data.staff_stats.receptionists;
                document.getElementById('assistants-count').textContent = data.staff_stats.assistants;
                document.getElementById('clients-count').textContent = data.staff_stats.clients;
            }
        })
        .catch(error => console.error('Error loading dashboard stats:', error));

    // Cargar estadísticas de citas
    const today = new Date().toISOString().split('T')[0];
    fetch(`/api/appointments/appointments/stats?date=${today}`, { headers })
        .then(response => response.json())
        .then(data => {
            if (data.appointment_stats) {
                document.getElementById('today-appointments').textContent = data.appointment_stats.today;
                document.getElementById('pending-appointments').textContent = data.appointment_stats.scheduled;
                document.getElementById('completed-appointments').textContent = data.appointment_stats.completed;
                document.getElementById('cancelled-appointments').textContent = data.appointment_stats.cancelled;
            }
        })
        .catch(error => console.error('Error loading appointment stats:', error));
}

// ===== PERSONAL =====

// Cargar lista de personal
function loadStaffList() {
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`
    };

    const roleFilter = document.getElementById('staff-role-filter').value;
    const statusFilter = document.getElementById('staff-status-filter').value;

    let url = '/api/admin/staff';
    if (roleFilter || statusFilter) {
        url += '?';
        if (roleFilter) {
            url += `role=${roleFilter}`;
        }
        if (roleFilter && statusFilter) {
            url += '&';
        }
        if (statusFilter) {
            url += `is_active=${statusFilter}`;
        }
    }

    fetch(url, { headers })
        .then(response => response.json())
        .then(data => {
            if (data.staff) {
                staffList = data.staff;
                renderStaffTable();
            }
        })
        .catch(error => console.error('Error loading staff list:', error));
}

// Renderizar tabla de personal
function renderStaffTable() {
    const tableBody = document.getElementById('staff-table-body');
    const searchText = document.getElementById('staff-search').value.toLowerCase();

    tableBody.innerHTML = '';

    const filteredStaff = staffList.filter(staff => {
        const fullName = `${staff.first_name} ${staff.last_name}`.toLowerCase();
        const email = staff.email.toLowerCase();
        return fullName.includes(searchText) || email.includes(searchText);
    });

    if (filteredStaff.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron resultados</td></tr>';
        return;
    }

    filteredStaff.forEach(staff => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = `${staff.first_name} ${staff.last_name}`;

        const emailCell = document.createElement('td');
        emailCell.textContent = staff.email;

        const phoneCell = document.createElement('td');
        phoneCell.textContent = staff.phone || 'N/A';

        const roleCell = document.createElement('td');
        roleCell.textContent = translateRole(staff.role);

        const specializationCell = document.createElement('td');
        specializationCell.textContent = staff.specialization || 'N/A';

        const statusCell = document.createElement('td');
        const statusBadge = document.createElement('span');
        statusBadge.classList.add('status-badge');
        statusBadge.classList.add(staff.is_active ? 'status-active' : 'status-inactive');
        statusBadge.textContent = staff.is_active ? 'Activo' : 'Inactivo';
        statusCell.appendChild(statusBadge);

        const actionsCell = document.createElement('td');
        const editButton = document.createElement('button');
        editButton.classList.add('btn', 'btn-sm', 'btn-primary', 'mr-1');
        editButton.textContent = 'Editar';
        editButton.onclick = () => editStaff(staff.id);

        const toggleButton = document.createElement('button');
        toggleButton.classList.add('btn', 'btn-sm');
        if (staff.is_active) {
            toggleButton.classList.add('btn-danger');
            toggleButton.textContent = 'Desactivar';
        } else {
            toggleButton.classList.add('btn-success');
            toggleButton.textContent = 'Activar';
        }
        toggleButton.onclick = () => toggleStaffStatus(staff.id, !staff.is_active);

        actionsCell.appendChild(editButton);
        actionsCell.appendChild(document.createTextNode(' '));
        actionsCell.appendChild(toggleButton);

        row.appendChild(nameCell);
        row.appendChild(emailCell);
        row.appendChild(phoneCell);
        row.appendChild(roleCell);
        row.appendChild(specializationCell);
        row.appendChild(statusCell);
        row.appendChild(actionsCell);

        tableBody.appendChild(row);
    });
}

// Filtrar personal
function filterStaff() {
    loadStaffList();
}

// Mostrar modal para agregar personal
function showAddStaffModal() {
    document.getElementById('staff-modal-title').textContent = 'Agregar Nuevo Personal';
    document.getElementById('staff-form').reset();
    document.getElementById('staff-id').value = '';
    document.getElementById('staff-modal').style.display = 'flex';
    toggleSpecializationField();
}

// Cerrar modal de personal
function closeStaffModal() {
    document.getElementById('staff-modal').style.display = 'none';
}

// Editar personal
function editStaff(staffId) {
    const staff = staffList.find(s => s.id === staffId);
    if (!staff) return;

    document.getElementById('staff-modal-title').textContent = 'Editar Personal';
    document.getElementById('staff-id').value = staff.id;
    document.getElementById('staff-email').value = staff.email;
    document.getElementById('staff-password').value = '';
    document.getElementById('staff-first-name').value = staff.first_name;
    document.getElementById('staff-last-name').value = staff.last_name;
    document.getElementById('staff-phone').value = staff.phone || '';
    document.getElementById('staff-role').value = staff.role;
    document.getElementById('staff-specialization').value = staff.specialization || '';
    document.getElementById('staff-active').value = staff.is_active.toString();

    toggleSpecializationField();
    document.getElementById('staff-modal').style.display = 'flex';
}

// Guardar personal
function saveStaff() {
    const staffId = document.getElementById('staff-id').value;
    const isNewStaff = !staffId;

    const staffData = {
        email: document.getElementById('staff-email').value,
        first_name: document.getElementById('staff-first-name').value,
        last_name: document.getElementById('staff-last-name').value,
        phone: document.getElementById('staff-phone').value,
        role: document.getElementById('staff-role').value,
        is_active: document.getElementById('staff-active').value === 'true'
    };

    // Agregar contraseña solo si se proporciona o es un nuevo miembro
    const password = document.getElementById('staff-password').value;
    if (password) {
        staffData.password = password;
    }

    // Agregar especialización solo para veterinarios
    if (staffData.role === 'veterinarian') {
        staffData.specialization = document.getElementById('staff-specialization').value;
    }

    const url = isNewStaff
        ? '/api/admin/staff'
        : `/api/admin/staff/${staffId}`;

    const method = isNewStaff ? 'POST' : 'PUT';

    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(staffData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        closeStaffModal();
        loadStaffList();
        alert(isNewStaff ? 'Personal agregado con éxito' : 'Personal actualizado con éxito');
    })
    .catch(error => {
        console.error('Error saving staff:', error);
        alert('Error al guardar. Por favor intente nuevamente.');
    });
}

// Cambiar estado de personal (activar/desactivar)
function toggleStaffStatus(staffId, newStatus) {
    if (!confirm(`¿Está seguro de ${newStatus ? 'activar' : 'desactivar'} a este miembro del personal?`)) {
        return;
    }

    fetch(`/api/admin/staff/${staffId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({ is_active: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        loadStaffList();
        alert(`El estado del personal ha sido ${newStatus ? 'activado' : 'desactivado'} exitosamente`);
    })
    .catch(error => {
        console.error('Error toggling staff status:', error);
        alert('Error al cambiar el estado. Por favor intente nuevamente.');
    });
}

// Mostrar/ocultar campo de especialización según rol
function toggleSpecializationField() {
    const role = document.getElementById('staff-role').value;
    const specializationGroup = document.getElementById('specialization-group');

    if (role === 'veterinarian') {
        specializationGroup.style.display = 'block';
    } else {
        specializationGroup.style.display = 'none';
    }
}

// ===== CLIENTES =====

// Cargar lista de clientes
function loadClientsList() {
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`
    };

    const statusFilter = document.getElementById('client-status-filter').value;

    let url = '/api/admin/clients';
    if (statusFilter) {
        url += `?is_active=${statusFilter}`;
    }

    fetch(url, { headers })
        .then(response => response.json())
        .then(data => {
            if (data.clients) {
                clientsList = data.clients;
                renderClientsTable();
            }
        })
        .catch(error => console.error('Error loading clients list:', error));
}

// Cargar estadísticas de clientes
function loadClientsStats() {
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`
    };

    // Cargar estadísticas básicas
    fetch('/api/admin/clients/stats', { headers })
        .then(response => response.json())
        .then(data => {
            if (data.stats) {
                document.getElementById('total-clients-count').textContent = data.stats.total || 0;
                document.getElementById('active-clients-count').textContent = data.stats.active || 0;
                document.getElementById('total-pets-count').textContent = data.stats.total_pets || 0;
                document.getElementById('avg-pets-per-client').textContent = data.stats.avg_pets_per_client?.toFixed(1) || '0.0';
            }
        })
        .catch(error => console.error('Error loading client stats:', error));
}

// Renderizar tabla de clientes
function renderClientsTable() {
    const tableBody = document.getElementById('clients-table-body');
    const searchText = document.getElementById('client-search').value.toLowerCase();

    tableBody.innerHTML = '';

    const filteredClients = clientsList.filter(client => {
        const fullName = `${client.first_name} ${client.last_name}`.toLowerCase();
        const email = client.email.toLowerCase();
        return fullName.includes(searchText) || email.includes(searchText);
    });

    if (filteredClients.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron resultados</td></tr>';
        return;
    }

    filteredClients.forEach(client => {
        // Obtener el conteo de mascotas y citas (datos simulados aquí)
        fetch(`/api/appointments/pets/${client.id}`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        })
        .then(response => response.json())
        .then(petsData => {
            // Obtener citas
            fetch(`/api/appointments/appointments?client_id=${client.id}`, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            .then(response => response.json())
            .then(appointmentsData => {
                const petCount = petsData.pets ? petsData.pets.length : 0;
                const appointmentCount = appointmentsData.appointments ? appointmentsData.appointments.length : 0;

                const row = document.createElement('tr');

                const nameCell = document.createElement('td');
                nameCell.textContent = `${client.first_name} ${client.last_name}`;

                const emailCell = document.createElement('td');
                emailCell.textContent = client.email;

                const phoneCell = document.createElement('td');
                phoneCell.textContent = client.phone || 'N/A';

                const petsCell = document.createElement('td');
                petsCell.textContent = petCount;

                const appointmentsCell = document.createElement('td');
                appointmentsCell.textContent = appointmentCount;

                const statusCell = document.createElement('td');
                const statusBadge = document.createElement('span');
                statusBadge.classList.add('status-badge');
                statusBadge.classList.add(client.is_active ? 'status-active' : 'status-inactive');
                statusBadge.textContent = client.is_active ? 'Activo' : 'Inactivo';
                statusCell.appendChild(statusBadge);

                const actionsCell = document.createElement('td');
                const viewButton = document.createElement('button');
                viewButton.classList.add('btn', 'btn-sm', 'btn-info', 'mr-1');
                viewButton.textContent = 'Ver Detalles';
                viewButton.onclick = () => viewClientDetails(client.id);

                const toggleButton = document.createElement('button');
                toggleButton.classList.add('btn', 'btn-sm');
                if (client.is_active) {
                    toggleButton.classList.add('btn-danger');
                    toggleButton.textContent = 'Desactivar';
                } else {
                    toggleButton.classList.add('btn-success');
                    toggleButton.textContent = 'Activar';
                }
                toggleButton.onclick = () => toggleClientStatus(client.id, !client.is_active);

                actionsCell.appendChild(viewButton);
                actionsCell.appendChild(document.createTextNode(' '));
                actionsCell.appendChild(toggleButton);

                row.appendChild(nameCell);
                row.appendChild(emailCell);
                row.appendChild(phoneCell);
                row.appendChild(petsCell);
                row.appendChild(appointmentsCell);
                row.appendChild(statusCell);
                row.appendChild(actionsCell);

                tableBody.appendChild(row);
            });
        });
    });
}

// Filtrar clientes
function filterClients() {
    loadClientsList();
}

// Ver detalles del cliente
function viewClientDetails(clientId) {
    currentClientId = clientId;
    const client = clientsList.find(c => c.id === clientId);

    if (!client) return;

    document.getElementById('client-details-title').textContent = `Cliente: ${client.first_name} ${client.last_name}`;
    document.getElementById('client-details-name').textContent = `${client.first_name} ${client.last_name}`;
    document.getElementById('client-details-email').textContent = client.email;
    document.getElementById('client-details-phone').textContent = client.phone || 'N/A';
    document.getElementById('client-details-created').textContent = formatDate(client.created_at);

    // Cargar mascotas del cliente
    loadClientPets(clientId);

    // Cargar historial de citas
    loadClientAppointments(clientId);

    // Mostrar modal
    document.getElementById('client-details-modal').style.display = 'flex';
}

// Cargar mascotas del cliente
function loadClientPets(clientId) {
    const petsList = document.getElementById('client-pets-list');
    petsList.innerHTML = '<p class="loading">Cargando mascotas...</p>';

    fetch(`/api/appointments/pets/${clientId}`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.pets || data.pets.length === 0) {
            petsList.innerHTML = '<p class="no-data">El cliente no tiene mascotas registradas</p>';
            return;
        }

        petsList.innerHTML = '';
        data.pets.forEach(pet => {
            const petCard = document.createElement('div');
            petCard.className = 'pet-card';

            const petIcon = document.createElement('div');
            petIcon.className = 'pet-icon';
            petIcon.textContent = getPetSpeciesIcon(pet.species);

            const petInfo = document.createElement('div');
            petInfo.className = 'pet-info';

            const petName = document.createElement('h5');
            petName.textContent = pet.name;

            const petDetails = document.createElement('p');
            petDetails.innerHTML = `
                <strong>Especie:</strong> ${pet.species}<br>
                <strong>Raza:</strong> ${pet.breed || 'N/A'}<br>
                <strong>Edad:</strong> ${pet.age ? `${pet.age} años` : 'N/A'}<br>
                <strong>Peso:</strong> ${pet.weight ? `${pet.weight} kg` : 'N/A'}
            `;

            petInfo.appendChild(petName);
            petInfo.appendChild(petDetails);

            petCard.appendChild(petIcon);
            petCard.appendChild(petInfo);

            petsList.appendChild(petCard);
        });
    })
    .catch(error => {
        console.error('Error loading client pets:', error);
        petsList.innerHTML = '<p class="error">Error al cargar mascotas</p>';
    });
}

// Cargar historial de citas del cliente
function loadClientAppointments(clientId) {
    const appointmentsList = document.getElementById('client-appointments-list');
    appointmentsList.innerHTML = '<p class="loading">Cargando historial de citas...</p>';

    fetch(`/api/appointments/appointments?client_id=${clientId}`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.appointments || data.appointments.length === 0) {
            appointmentsList.innerHTML = '<p class="no-data">El cliente no tiene citas registradas</p>';
            return;
        }

        appointmentsList.innerHTML = '';

        // Ordenar citas por fecha (más recientes primero)
        const sortedAppointments = data.appointments.sort((a, b) => {
            return new Date(b.appointment_date) - new Date(a.appointment_date);
        });

        sortedAppointments.forEach(appointment => {
            const appointmentItem = document.createElement('div');
            appointmentItem.className = 'appointment-item';
            appointmentItem.classList.add(`status-${appointment.status}`);

            const dateTime = document.createElement('div');
            dateTime.className = 'appointment-date-time';
            dateTime.innerHTML = `
                <strong>${formatDate(appointment.appointment_date)}</strong> a las 
                <strong>${formatTime(appointment.appointment_time)}</strong>
            `;

            const details = document.createElement('div');
            details.className = 'appointment-details';
            details.innerHTML = `
                <p><strong>Veterinario:</strong> ID ${appointment.veterinarian_id}</p>
                <p><strong>Mascota:</strong> ID ${appointment.pet_id}</p>
                <p><strong>Motivo:</strong> ${appointment.reason || 'No especificado'}</p>
                <p><strong>Estado:</strong> <span class="status-badge status-${appointment.status}">${translateStatus(appointment.status)}</span></p>
            `;

            if (appointment.notes) {
                const notes = document.createElement('div');
                notes.className = 'appointment-notes';
                notes.innerHTML = `<strong>Notas:</strong> ${appointment.notes}`;
                details.appendChild(notes);
            }

            appointmentItem.appendChild(dateTime);
            appointmentItem.appendChild(details);

            appointmentsList.appendChild(appointmentItem);
        });
    })
    .catch(error => {
        console.error('Error loading client appointments:', error);
        appointmentsList.innerHTML = '<p class="error">Error al cargar historial de citas</p>';
    });
}

// Cerrar modal de detalles del cliente
function closeClientDetailsModal() {
    document.getElementById('client-details-modal').style.display = 'none';
    currentClientId = null;
}

// Cambiar estado del cliente
function toggleClientStatus() {
    if (!currentClientId) return;

    const client = clientsList.find(c => c.id === currentClientId);
    if (!client) return;

    const newStatus = !client.is_active;

    if (!confirm(`¿Está seguro de ${newStatus ? 'activar' : 'desactivar'} a este cliente?`)) {
        return;
    }

    fetch(`/api/admin/clients/${currentClientId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({ is_active: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        closeClientDetailsModal();
        loadClientsList();
        loadClientsStats();
        alert(`El cliente ha sido ${newStatus ? 'activado' : 'desactivado'} exitosamente`);
    })
    .catch(error => {
        console.error('Error toggling client status:', error);
        alert('Error al cambiar el estado del cliente. Por favor intente nuevamente.');
    });
}

// ===== HORARIOS =====

// Cargar personal para selección de horarios
function loadStaffForSchedules() {
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`
    };

    fetch('/api/admin/staff?role=veterinarian&is_active=true', { headers })
        .then(response => response.json())
        .then(data => {
            if (!data.staff) return;

            const selectElement = document.getElementById('schedule-staff-filter');
            selectElement.innerHTML = '<option value="">Seleccione un miembro del personal</option>';

            data.staff.forEach(staff => {
                const option = document.createElement('option');
                option.value = staff.id;
                option.textContent = `${staff.first_name} ${staff.last_name} - ${staff.specialization || 'Sin especialidad'}`;
                selectElement.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading staff for schedules:', error));
}

// Cargar horarios de un miembro del personal
function loadStaffSchedules() {
    const staffId = document.getElementById('schedule-staff-filter').value;
    if (!staffId) {
        alert('Por favor seleccione un miembro del personal');
        return;
    }

    // Obtener el nombre del staff para mostrar
    const staffSelect = document.getElementById('schedule-staff-filter');
    const staffName = staffSelect.options[staffSelect.selectedIndex].text;

    fetch(`/api/schedules/staff-schedules/${staffId}`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('schedule-staff-name').textContent = staffName;
        document.getElementById('schedule-editor').style.display = 'block';

        // Limpiar todos los contenedores de horarios
        document.querySelectorAll('.schedule-slots').forEach(container => {
            container.innerHTML = '';
        });

        // Guardar los horarios actuales en variable global
        currentStaffSchedules = {};

        // Inicializar todos los días como no configurados
        for (let i = 0; i < 7; i++) {
            const container = document.getElementById(`schedule-day-${i}`);
            container.innerHTML = '<div class="schedule-not-configured">Horario no configurado</div>';
        }

        if (data.schedules && data.schedules.length > 0) {
            data.schedules.forEach(schedule => {
                currentStaffSchedules[schedule.day_of_week] = schedule;

                const container = document.getElementById(`schedule-day-${schedule.day_of_week}`);

                if (schedule.is_available) {
                    container.innerHTML = `
                        <div class="schedule-time-range">
                            <span>${formatTime(schedule.start_time)} - ${formatTime(schedule.end_time)}</span>
                        </div>
                        ${schedule.break_start ? `
                        <div class="schedule-break">
                            <span>Descanso: ${formatTime(schedule.break_start)} - ${formatTime(schedule.break_end)}</span>
                        </div>
                        ` : ''}
                        <div class="schedule-info">
                            <span>Citas: ${schedule.appointment_duration} min (máx: ${schedule.max_appointments})</span>
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="schedule-not-available">No disponible</div>';
                }
            });
        }
    })
    .catch(error => {
        console.error('Error loading staff schedules:', error);
        alert('Error al cargar los horarios. Por favor intente nuevamente.');
    });
}

// Editar horario de un día
function editDaySchedule(dayOfWeek) {
    const staffId = document.getElementById('schedule-staff-filter').value;
    if (!staffId) {
        alert('Por favor seleccione un miembro del personal');
        return;
    }

    document.getElementById('schedule-day-modal-title').textContent = `Editar Horario - ${getDayName(dayOfWeek)}`;
    document.getElementById('schedule-staff-id').value = staffId;
    document.getElementById('schedule-day-of-week').value = dayOfWeek;

    // Establecer valores por defecto
    document.getElementById('schedule-available').value = 'true';
    document.getElementById('schedule-start-time').value = '09:00';
    document.getElementById('schedule-end-time').value = '17:00';
    document.getElementById('schedule-has-break').checked = false;
    document.getElementById('break-times-container').style.display = 'none';
    document.getElementById('schedule-break-start').value = '13:00';
    document.getElementById('schedule-break-end').value = '14:00';
    document.getElementById('schedule-appointment-duration').value = '30';
    document.getElementById('schedule-max-appointments').value = '8';
    document.getElementById('schedule-id').value = '';

// Si hay un horario existente, cargar sus valores
    if (currentStaffSchedules[dayOfWeek]) {
        const schedule = currentStaffSchedules[dayOfWeek];
        document.getElementById('schedule-id').value = schedule.id;
        document.getElementById('schedule-available').value = schedule.is_available.toString();
        document.getElementById('schedule-start-time').value = formatTimeForInput(schedule.start_time);
        document.getElementById('schedule-end-time').value = formatTimeForInput(schedule.end_time);

        const hasBreak = schedule.break_start && schedule.break_end;
        document.getElementById('schedule-has-break').checked = hasBreak;
        if (hasBreak) {
            document.getElementById('break-times-container').style.display = 'block';
            document.getElementById('schedule-break-start').value = formatTimeForInput(schedule.break_start);
            document.getElementById('schedule-break-end').value = formatTimeForInput(schedule.break_end);
        }

        document.getElementById('schedule-appointment-duration').value = schedule.appointment_duration;
        document.getElementById('schedule-max-appointments').value = schedule.max_appointments;
    }

    toggleScheduleTimes();
    document.getElementById('schedule-day-modal').style.display = 'flex';
}

// Guardar horario de un día
function saveScheduleDay() {
    const staffId = document.getElementById('schedule-staff-id').value;
    const dayOfWeek = document.getElementById('schedule-day-of-week').value;
    const scheduleId = document.getElementById('schedule-id').value;
    const isAvailable = document.getElementById('schedule-available').value === 'true';

    let scheduleData = {
        staff_id: parseInt(staffId),
        day_of_week: parseInt(dayOfWeek),
        is_available: isAvailable
    };

    if (isAvailable) {
        scheduleData.start_time = document.getElementById('schedule-start-time').value;
        scheduleData.end_time = document.getElementById('schedule-end-time').value;
        scheduleData.appointment_duration = parseInt(document.getElementById('schedule-appointment-duration').value);
        scheduleData.max_appointments = parseInt(document.getElementById('schedule-max-appointments').value);

        const hasBreak = document.getElementById('schedule-has-break').checked;
        if (hasBreak) {
            scheduleData.break_start = document.getElementById('schedule-break-start').value;
            scheduleData.break_end = document.getElementById('schedule-break-end').value;
        } else {
            scheduleData.break_start = null;
            scheduleData.break_end = null;
        }
    }

    const url = scheduleId
        ? `/api/schedules/staff-schedules/${scheduleId}`
        : '/api/schedules/staff-schedules';

    const method = scheduleId ? 'PUT' : 'POST';

    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(scheduleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        closeScheduleDayModal();
        loadStaffSchedules();
        alert('Horario guardado exitosamente');
    })
    .catch(error => {
        console.error('Error saving schedule:', error);
        alert('Error al guardar el horario. Por favor intente nuevamente.');
    });
}

// Cerrar modal de edición de horario
function closeScheduleDayModal() {
    document.getElementById('schedule-day-modal').style.display = 'none';
}

// Mostrar/ocultar campos de horario según disponibilidad
function toggleScheduleTimes() {
    const isAvailable = document.getElementById('schedule-available').value === 'true';
    document.getElementById('schedule-times-container').style.display = isAvailable ? 'block' : 'none';
}

// Mostrar/ocultar campos de descanso
function toggleBreakTimes() {
    const hasBreak = document.getElementById('schedule-has-break').checked;
    document.getElementById('break-times-container').style.display = hasBreak ? 'block' : 'none';
}

// Copiar horario
function copySchedule() {
    const staffId = document.getElementById('schedule-staff-filter').value;
    if (!staffId) {
        alert('Por favor seleccione un miembro del personal');
        return;
    }

    // Verificar si tiene horarios configurados
    if (Object.keys(currentStaffSchedules).length === 0) {
        alert('No hay horarios configurados para copiar');
        return;
    }

    // Obtener el nombre del staff para mostrar
    const staffSelect = document.getElementById('schedule-staff-filter');
    const staffName = staffSelect.options[staffSelect.selectedIndex].text;

    document.getElementById('copy-source-staff-id').value = staffId;
    document.getElementById('copy-source-staff-name').textContent = staffName;

    // Cargar personal para selección de destino
    loadStaffForCopy();

    document.getElementById('copy-schedule-modal').style.display = 'flex';
}

// Cargar personal para selección de destino de copia
function loadStaffForCopy() {
    const sourceStaffId = document.getElementById('copy-source-staff-id').value;
    const headers = {
        'Authorization': `Bearer ${getAuthToken()}`
    };

    fetch('/api/admin/staff?is_active=true', { headers })
        .then(response => response.json())
        .then(data => {
            if (!data.staff) return;

            const selectElement = document.getElementById('copy-target-staff');
            selectElement.innerHTML = '';

            data.staff.forEach(staff => {
                // No incluir al personal de origen en la lista
                if (staff.id.toString() === sourceStaffId) return;

                const option = document.createElement('option');
                option.value = staff.id;
                option.textContent = `${staff.first_name} ${staff.last_name} - ${translateRole(staff.role)}`;
                selectElement.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading staff for copy:', error));
}

// Cambiar objetivo de copia (personal específico o rol)
function toggleCopyTarget(target) {
    document.getElementById('copy-to-staff-container').style.display = (target === 'staff') ? 'block' : 'none';
    document.getElementById('copy-to-role-container').style.display = (target === 'role') ? 'block' : 'none';
}

// Ejecutar la copia de horarios
function executeCopySchedule() {
    const sourceStaffId = document.getElementById('copy-source-staff-id').value;
    const copyToStaff = document.getElementById('copy-to-staff').checked;

    let copyData = {
        source_staff_id: parseInt(sourceStaffId)
    };

    if (copyToStaff) {
        const select = document.getElementById('copy-target-staff');
        const selectedOptions = Array.from(select.selectedOptions).map(option => parseInt(option.value));

        if (selectedOptions.length === 0) {
            alert('Por favor seleccione al menos un miembro del personal');
            return;
        }

        copyData.target_staff_ids = selectedOptions;
    } else {
        const targetRole = document.getElementById('copy-target-role').value;

        if (!targetRole) {
            alert('Por favor seleccione un rol');
            return;
        }

        copyData.target_role = targetRole;
    }

    fetch('/api/schedules/staff-schedules/copy', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(copyData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        closeCopyScheduleModal();
        alert(`Horarios copiados: ${data.success_count} exitosos, ${data.error_count} fallidos`);
    })
    .catch(error => {
        console.error('Error copying schedules:', error);
        alert('Error al copiar horarios. Por favor intente nuevamente.');
    });
}

// Cerrar modal de copia de horarios
function closeCopyScheduleModal() {
    document.getElementById('copy-schedule-modal').style.display = 'none';
}

// ===== CONFIGURACIÓN =====

// Cargar configuración del sistema
function loadSystemSettings() {
    fetch('/api/admin/settings', {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.settings) return;

        systemSettings = data.settings;

        // Configuración general
        document.getElementById('clinic-name').value = getSetting('clinic_name', 'Clínica Veterinaria');
        document.getElementById('business-hours-start').value = formatTimeForInput(getSetting('business_hours_start', '09:00'));
        document.getElementById('business-hours-end').value = formatTimeForInput(getSetting('business_hours_end', '18:00'));
        document.getElementById('appointment-duration').value = getSetting('appointment_duration', 30);
        document.getElementById('max-appointments-per-day').value = getSetting('max_appointments_per_day', 20);

        // Configuración de notificaciones
        document.getElementById('email-notifications').value = getSetting('email_notifications', 'true');
        document.getElementById('reminder-hours').value = getSetting('reminder_hours', 24);
        document.getElementById('email-template').value = getSetting('email_template', 'Estimado(a) {{nombre}},\n\nLe recordamos su cita programada para el {{fecha}} a las {{hora}}.\n\nSaludos cordiales,\nClínica Veterinaria');
    })
    .catch(error => {
        console.error('Error loading system settings:', error);
        alert('Error al cargar la configuración del sistema. Por favor intente nuevamente.');
    });
}

// Guardar configuración general
function saveGeneralSettings() {
    const settings = {
        clinic_name: document.getElementById('clinic-name').value,
        business_hours_start: document.getElementById('business-hours-start').value,
        business_hours_end: document.getElementById('business-hours-end').value,
        appointment_duration: parseInt(document.getElementById('appointment-duration').value),
        max_appointments_per_day: parseInt(document.getElementById('max-appointments-per-day').value)
    };

    fetch('/api/admin/settings/general', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        alert('Configuración general guardada exitosamente');
        loadSystemSettings();
    })
    .catch(error => {
        console.error('Error saving general settings:', error);
        alert('Error al guardar la configuración general. Por favor intente nuevamente.');
    });
}

// Guardar configuración de notificaciones
function saveNotificationSettings() {
    const settings = {
        email_notifications: document.getElementById('email-notifications').value,
        reminder_hours: parseInt(document.getElementById('reminder-hours').value),
        email_template: document.getElementById('email-template').value
    };

    fetch('/api/admin/settings/notifications', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        alert('Configuración de notificaciones guardada exitosamente');
        loadSystemSettings();
    })
    .catch(error => {
        console.error('Error saving notification settings:', error);
        alert('Error al guardar la configuración de notificaciones. Por favor intente nuevamente.');
    });
}

// Generar respaldo de la base de datos
function generateBackup() {
    fetch('/api/admin/settings/backup', {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error al generar respaldo');
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;

        // Nombre del archivo con fecha
        const date = new Date();
        const dateStr = date.toISOString().split('T')[0];
        a.download = `veterinary_backup_${dateStr}.sql`;

        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

        alert('Respaldo generado exitosamente');
    })
    .catch(error => {
        console.error('Error generating backup:', error);
        alert('Error al generar el respaldo. Por favor intente nuevamente.');
    });
}

// Restaurar desde respaldo
function restoreFromBackup() {
    const fileInput = document.getElementById('restore-file');

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Por favor seleccione un archivo de respaldo');
        return;
    }

    if (!confirm('¿Está seguro de restaurar la base de datos? Esta acción sobrescribirá todos los datos actuales.')) {
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('backup_file', file);

    fetch('/api/admin/settings/restore', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        alert('Restauración completada exitosamente. La página se recargará.');
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    })
    .catch(error => {
        console.error('Error restoring from backup:', error);
        alert('Error al restaurar desde el respaldo. Por favor intente nuevamente.');
    });
}

// ===== UTILIDADES =====

// Obtener token de autenticación
function getAuthToken() {
    return localStorage.getItem('authToken') || sessionStorage.getItem('authToken') || '';
}

// Formatear fecha
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';

    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Formatear hora
function formatTime(timeStr) {
    if (!timeStr) return 'N/A';

    // Si ya tiene formato HH:MM:SS o HH:MM
    if (timeStr.includes(':')) {
        const [hours, minutes] = timeStr.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour % 12 || 12;

        return `${hour12}:${minutes} ${ampm}`;
    }

    return timeStr;
}

// Formatear hora para inputs
function formatTimeForInput(timeStr) {
    if (!timeStr) return '';

    // Si ya tiene formato HH:MM:SS o HH:MM
    if (timeStr.includes(':')) {
        const parts = timeStr.split(':');
        return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`;
    }

    return timeStr;
}

// Obtener nombre del día
function getDayName(dayOfWeek) {
    const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    return days[dayOfWeek] || 'Desconocido';
}

// Traducir rol
function translateRole(role) {
    const translations = {
        'admin': 'Administrador',
        'veterinarian': 'Veterinario',
        'receptionist': 'Recepcionista',
        'assistant': 'Auxiliar',
        'client': 'Cliente'
    };

    return translations[role] || role;
}

// Traducir estado de cita
function translateStatus(status) {
    const translations = {
        'scheduled': 'Programada',
        'completed': 'Completada',
        'cancelled': 'Cancelada',
        'no-show': 'No asistió'
    };

    return translations[status] || status;
}

// Obtener ícono según especie de mascota
function getPetSpeciesIcon(species) {
    const icons = {
        'perro': '🐕',
        'perros': '🐕',
        'dog': '🐕',
        'dogs': '🐕',
        'gato': '🐈',
        'gatos': '🐈',
        'cat': '🐈',
        'cats': '🐈',
        'ave': '🐦',
        'aves': '🐦',
        'bird': '🐦',
        'birds': '🐦',
        'pez': '🐠',
        'peces': '🐠',
        'fish': '🐠',
        'conejo': '🐇',
        'conejos': '🐇',
        'rabbit': '🐇',
        'rabbits': '🐇',
        'reptil': '🦎',
        'reptiles': '🦎',
        'reptile': '🦎',
        'hamster': '🐹',
        'hamsters': '🐹',
        'another': '🐾',
        'otros': '🐾',
        'otro': '🐾',
        'other': '🐾'
    };

    const speciesLower = species.toLowerCase();
    return icons[speciesLower] || '🐾';
}

// Obtener valor de configuración
function getSetting(key, defaultValue) {
    if (!systemSettings || !systemSettings[key]) {
        return defaultValue;
    }
    return systemSettings[key];
}

// Función para configurar los escuchadores de eventos
function setupEventListeners() {
    // Escuchadores para filtros y búsquedas
    const staffRoleFilter = document.getElementById('staff-role-filter');
    if (staffRoleFilter) {
        staffRoleFilter.addEventListener('change', filterStaff);
    }

    const staffStatusFilter = document.getElementById('staff-status-filter');
    if (staffStatusFilter) {
        staffStatusFilter.addEventListener('change', filterStaff);
    }

    const clientStatusFilter = document.getElementById('client-status-filter');
    if (clientStatusFilter) {
        clientStatusFilter.addEventListener('change', filterClients);
    }

    // Manejar el cierre de modales al hacer clic fuera del contenido
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(event) {
            if (event.target === this) {
                this.style.display = 'none';
            }
        });
    });

    // Activar la primera pestaña por defecto
    switchTab('dashboard');
}