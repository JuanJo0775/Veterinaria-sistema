# frontend/app.py
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
import requests
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuración de URLs de servicios
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5001')
APPOINTMENT_SERVICE_URL = os.getenv('APPOINTMENT_SERVICE_URL', 'http://appointment-service:5002')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service:5003')


# Decorador para rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session:
            flash('Por favor inicia sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Llamar al servicio de autenticación
        response = requests.post(f'{AUTH_SERVICE_URL}/api/auth/login', json={
            'email': email,
            'password': password
        })

        if response.status_code == 200:
            data = response.json()
            session['token'] = data['access_token']
            session['user'] = data['user']
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = {
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone': request.form.get('phone'),
            'role': request.form.get('role'),
            'specialization': request.form.get('specialization')
        }

        # Llamar al servicio de autenticación
        response = requests.post(f'{AUTH_SERVICE_URL}/api/auth/register', json=form_data)

        if response.status_code == 201:
            data = response.json()
            session['token'] = data['access_token']
            session['user'] = data['user']
            flash('Registro exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Error en el registro', 'danger')

    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    headers = {'Authorization': f'Bearer {session["token"]}'}

    # Obtener citas del usuario
    if user['role'] == 'client':
        response = requests.get(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?client_id={user["id"]}',
            headers=headers
        )
    else:  # veterinarian
        response = requests.get(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?veterinarian_id={user["id"]}',
            headers=headers
        )

    appointments = response.json().get('appointments', []) if response.status_code == 200 else []

    # Obtener notificaciones
    notif_response = requests.get(
        f'{NOTIFICATION_SERVICE_URL}/api/notifications/notifications/{user["id"]}?status=pending',
    )
    notifications = notif_response.json().get('notifications', []) if notif_response.status_code == 200 else []

    return render_template('dashboard.html', user=user, appointments=appointments, notifications=notifications)


@app.route('/appointment/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    user = session.get('user')
    token = session.get('token')
    headers = {'Authorization': f'Bearer {token}'}

    if user['role'] != 'client':
        flash('Solo los clientes pueden agendar citas', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        appointment_data = {
            'client_id': user['id'],
            'veterinarian_id': int(request.form.get('veterinarian_id')),
            'pet_id': int(request.form.get('pet_id')),
            'appointment_date': request.form.get('appointment_date'),
            'appointment_time': request.form.get('appointment_time'),
            'reason': request.form.get('reason')
        }

        # Crear cita
        response = requests.post(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments',
            json=appointment_data,
            headers=headers
        )

        if response.status_code == 201:
            appointment = response.json()['appointment']

            # Enviar notificación por email
            requests.post(f'{NOTIFICATION_SERVICE_URL}/api/notifications/send-email', json={
                'type': 'appointment_confirmation',
                'recipient_email': user['email'],
                'appointment_details': {
                    'user_id': user['id'],
                    'appointment_id': appointment['id'],
                    'client_name': f"{user['first_name']} {user['last_name']}",
                    'date': appointment['appointment_date'],
                    'time': appointment['appointment_time'],
                    'veterinarian_name': 'Dr. Veterinario',  # Obtener del servicio de auth
                    'pet_name': 'Mascota',  # Obtener del servicio de citas
                    'reason': appointment['reason']
                }
            })

            flash('Cita agendada exitosamente', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Error al agendar la cita', 'danger')

    # Obtener veterinarios disponibles
    vet_response = requests.get(f'{AUTH_SERVICE_URL}/api/auth/veterinarians')
    veterinarians = vet_response.json().get('veterinarians', []) if vet_response.status_code == 200 else []

    # Obtener mascotas del usuario
    pets_response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/pets/{user["id"]}',
        headers=headers
    )
    pets = pets_response.json().get('pets', []) if pets_response.status_code == 200 else []

    return render_template('appointment.html',
                           veterinarians=veterinarians,
                           pets=pets,
                           user=user,
                           token=token)


@app.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    headers = {'Authorization': f'Bearer {session["token"]}'}

    response = requests.delete(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments/{appointment_id}',
        headers=headers
    )

    if response.status_code == 200:
        flash('Cita cancelada exitosamente', 'success')
    else:
        flash('Error al cancelar la cita', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('index'))


@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'frontend'}, 200


# Nueva ruta para manejar la creación de mascotas
@app.route('/api/appointments/pets', methods=['POST'])
@login_required
def create_pet_proxy():
    """Proxy para redirigir la llamada al servicio de appointments"""
    token = session.get('token')

    if not token:
        return jsonify({'error': 'No hay sesión activa'}), 401

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Debug logging
    app.logger.info(f"Creating pet with data: {request.json}")
    app.logger.info(f"Token present: {bool(token)}")

    # Redirigir la solicitud al servicio de appointments
    try:
        response = requests.post(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/pets',
            json=request.json,
            headers=headers
        )

        app.logger.info(f"Response from appointment service: {response.status_code}")
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error creating pet: {str(e)}")
        return jsonify({'error': 'Error al comunicarse con el servicio'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)