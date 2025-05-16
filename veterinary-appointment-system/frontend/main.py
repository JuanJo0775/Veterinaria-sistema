# frontend/main.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
import requests
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = 'dev-secret-key-for-local-frontend'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# Configuración de URLs de servicios para desarrollo local
AUTH_SERVICE_URL = 'http://localhost:5001'
APPOINTMENT_SERVICE_URL = 'http://localhost:5002'
NOTIFICATION_SERVICE_URL = 'http://localhost:5003'

# Copiar todas las rutas del archivo app.py original aquí

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

    if user['role'] == 'client':
        response = requests.get(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?client_id={user["id"]}',
            headers=headers
        )
    else:
        response = requests.get(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?veterinarian_id={user["id"]}',
            headers=headers
        )

    appointments = response.json().get('appointments', []) if response.status_code == 200 else []

    notif_response = requests.get(
        f'{NOTIFICATION_SERVICE_URL}/api/notifications/notifications/{user["id"]}?status=pending',
    )
    notifications = notif_response.json().get('notifications', []) if notif_response.status_code == 200 else []

    return render_template('dashboard.html', user=user, appointments=appointments, notifications=notifications)

@app.route('/appointment/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    user = session.get('user')
    headers = {'Authorization': f'Bearer {session["token"]}'}

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

        response = requests.post(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments',
            json=appointment_data,
            headers=headers
        )

        if response.status_code == 201:
            appointment = response.json()['appointment']

            requests.post(f'{NOTIFICATION_SERVICE_URL}/api/notifications/send-email', json={
                'type': 'appointment_confirmation',
                'recipient_email': user['email'],
                'appointment_details': {
                    'user_id': user['id'],
                    'appointment_id': appointment['id'],
                    'client_name': f"{user['first_name']} {user['last_name']}",
                    'date': appointment['appointment_date'],
                    'time': appointment['appointment_time'],
                    'veterinarian_name': 'Dr. Veterinario',
                    'pet_name': 'Mascota',
                    'reason': appointment['reason']
                }
            })

            flash('Cita agendada exitosamente', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Error al agendar la cita', 'danger')

    vet_response = requests.get(f'{AUTH_SERVICE_URL}/api/auth/veterinarians')
    veterinarians = vet_response.json().get('veterinarians', []) if vet_response.status_code == 200 else []

    pets_response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/pets/{user["id"]}',
        headers=headers
    )
    pets = pets_response.json().get('pets', []) if pets_response.status_code == 200 else []

    return render_template('appointment.html',
                           veterinarians=veterinarians,
                           pets=pets,
                           user=user)

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

@app.route('/api/appointments/pets', methods=['POST', 'OPTIONS'])
def create_pet_proxy():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
    else:
        token = session.get('token')

    if not token:
        app.logger.error("No token found in request or session")
        return jsonify({'error': 'No hay sesión activa'}), 401

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/pets',
            json=request.json,
            headers=headers
        )

        result = jsonify(response.json())
        result.headers.add('Access-Control-Allow-Origin', '*')
        return result, response.status_code
    except Exception as e:
        app.logger.error(f"Error creating pet: {str(e)}")
        return jsonify({'error': 'Error al comunicarse con el servicio'}), 500

@app.route('/api/appointments/available-slots/<int:veterinarian_id>')
@login_required
def get_available_slots_proxy(veterinarian_id):
    token = session.get('token')
    date = request.args.get('date')

    if not token:
        return jsonify({'error': 'No hay sesión activa'}), 401

    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(
            f'{APPOINTMENT_SERVICE_URL}/api/appointments/available-slots/{veterinarian_id}?date={date}',
            headers=headers
        )
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error getting available slots: {str(e)}")
        return jsonify({'error': 'Error al obtener horarios disponibles'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)