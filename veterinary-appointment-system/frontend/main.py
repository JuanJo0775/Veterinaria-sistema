    # frontend/main.py
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, make_response
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

            # Redireccionar según el rol del usuario
            role = data['user']['role']
            if role == 'admin':
                return redirect(url_for('admin_panel'))
            elif role == 'veterinarian':
                return redirect(url_for('vet_dashboard'))
            elif role == 'receptionist':
                return redirect(url_for('receptionist_dashboard'))
            elif role == 'assistant':
                return redirect(url_for('assistant_dashboard'))
            else:  # cliente
                return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas', 'danger')

    return render_template('login.html')


# frontend/main.py - RUTA DE REGISTRO CORREGIDA
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener datos del formulario
        form_data = {
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password', ''),
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip() or None
        }

        # Validación básica
        if not all([form_data['email'], form_data['password'], form_data['first_name'], form_data['last_name']]):
            flash('Por favor complete todos los campos obligatorios', 'danger')
            return render_template('register.html')

        if len(form_data['password']) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('register.html')

        # Verificar formato de email básico
        if '@' not in form_data['email'] or '.' not in form_data['email']:
            flash('Por favor ingrese un email válido', 'danger')
            return render_template('register.html')

        try:
            # Llamar al servicio de autenticación
            response = requests.post(
                f'{AUTH_SERVICE_URL}/api/auth/register',
                json=form_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")

            if response.status_code == 201:
                data = response.json()
                session['token'] = data['access_token']
                session['user'] = data['user']
                flash('Registro exitoso. ¡Bienvenido!', 'success')
                return redirect(url_for('dashboard'))
            else:
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        flash(f'Error: {error_data["error"]}', 'danger')
                    elif 'errors' in error_data:
                        # Errores de validación de marshmallow
                        for field, messages in error_data['errors'].items():
                            for message in messages:
                                flash(f'{field}: {message}', 'danger')
                    else:
                        flash('Error en el registro. Por favor intente nuevamente.', 'danger')
                except:
                    flash(f'Error del servidor (código {response.status_code})', 'danger')

        except requests.exceptions.Timeout:
            flash('Error: El servidor tardó demasiado en responder. Intente nuevamente.', 'danger')
        except requests.exceptions.ConnectionError:
            flash('Error: No se pudo conectar al servidor. Verifique que el servicio de autenticación esté funcionando.', 'danger')
        except requests.exceptions.RequestException as e:
            flash(f'Error de conexión: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {str(e)}', 'danger')

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


#
# PANEL DE ADMINISTRADOR
#

@app.route('/admin')
@login_required
def admin_panel():
    """Panel de administración (solo para administradores)"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        flash('Acceso no autorizado. Se requieren privilegios de administrador.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('admin_panel.html', user=user)


@app.route('/api/admin/dashboard/stats')
@login_required
def admin_dashboard_stats():
    """API para estadísticas del panel de administración"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Reenviar la petición al servicio de autenticación
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.get(f'{AUTH_SERVICE_URL}/api/admin/dashboard/stats', headers=headers)
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error obteniendo estadísticas: {str(e)}")
        # Devolver datos simulados si hay un error
        return jsonify({
            'staff_stats': {
                'veterinarians': 2,
                'receptionists': 1,
                'assistants': 1,
                'clients': 2,
                'total_staff': 4
            }
        }), 200


@app.route('/api/admin/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def admin_api_proxy(path):
    """Proxy para las rutas de administración"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Reenviar la petición al servicio correspondiente
    headers = {
        'Authorization': f'Bearer {session["token"]}',
        'Content-Type': 'application/json'
    }

    url = f'{AUTH_SERVICE_URL}/api/admin/{path}'

    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers, params=request.args)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, json=request.json)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, json=request.json)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return jsonify({'error': 'Método no soportado'}), 405

        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error en proxy de administración: {str(e)}")
        # Si el endpoint es staff, devolver datos simulados
        if 'staff' in path:
            if request.method == 'GET':
                return jsonify({
                    'staff': [
                        {
                            'id': 1,
                            'email': 'admin@veterinary.com',
                            'first_name': 'Admin',
                            'last_name': 'Sistema',
                            'phone': '555-ADMIN',
                            'role': 'admin',
                            'specialization': None,
                            'is_active': True
                        },
                        {
                            'id': 2,
                            'email': 'vet1@veterinary.com',
                            'first_name': 'Dr. Juan',
                            'last_name': 'García',
                            'phone': '555-0101',
                            'role': 'veterinarian',
                            'specialization': 'Cirugía General',
                            'is_active': True
                        }
                    ]
                }), 200
            elif request.method == 'POST' or request.method == 'PUT':
                return jsonify({
                    'message': 'Operación simulada exitosa',
                    'user': request.json
                }), 200

        return jsonify({'error': 'Error de comunicación con el servicio'}), 500


@app.route('/api/schedules/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def schedules_api_proxy(path):
    """Proxy para las rutas de horarios"""
    headers = {
        'Authorization': f'Bearer {session["token"]}',
        'Content-Type': 'application/json'
    }

    url = f'{APPOINTMENT_SERVICE_URL}/api/schedules/{path}'

    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers, params=request.args)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, json=request.json)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, json=request.json)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return jsonify({'error': 'Método no soportado'}), 405

        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error en proxy de horarios: {str(e)}")

        # Si el endpoint es staff-schedules, devolver datos simulados
        if 'staff-schedules' in path:
            if request.method == 'GET':
                return jsonify({
                    'schedules': [
                        {
                            'id': 1,
                            'staff_id': int(path.split('/')[-1]) if path.split('/')[-1].isdigit() else 2,
                            'day_of_week': 0,  # Lunes
                            'start_time': '09:00:00',
                            'end_time': '17:00:00',
                            'break_start': '13:00:00',
                            'break_end': '14:00:00',
                            'max_appointments': 8,
                            'appointment_duration': 30,
                            'is_available': True
                        },
                        {
                            'id': 2,
                            'staff_id': int(path.split('/')[-1]) if path.split('/')[-1].isdigit() else 2,
                            'day_of_week': 1,  # Martes
                            'start_time': '09:00:00',
                            'end_time': '17:00:00',
                            'break_start': '13:00:00',
                            'break_end': '14:00:00',
                            'max_appointments': 8,
                            'appointment_duration': 30,
                            'is_available': True
                        }
                    ]
                }), 200
            else:
                return jsonify({
                    'message': 'Operación simulada exitosa',
                    'schedule': request.json
                }), 200

        return jsonify({'error': 'Error de comunicación con el servicio'}), 500


# Proxy para estadísticas de clientes
@app.route('/api/admin/clients/stats')
@login_required
def admin_client_stats():
    """API para estadísticas de clientes"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Datos simulados
    return jsonify({
        'stats': {
            'total': 10,
            'active': 8,
            'total_pets': 15,
            'avg_pets_per_client': 1.5
        }
    }), 200


# Proxy para obtener configuración del sistema
@app.route('/api/admin/settings')
@login_required
def admin_get_settings():
    """API para obtener configuración del sistema"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Datos simulados para configuración
    settings = {
        'clinic_name': 'Clínica Veterinaria',
        'business_hours_start': '09:00',
        'business_hours_end': '18:00',
        'appointment_duration': 30,
        'max_appointments_per_day': 20,
        'email_notifications': 'true',
        'reminder_hours': 24,
        'email_template': 'Estimado(a) {{nombre}},\n\nLe recordamos su cita programada para el {{fecha}} a las {{hora}}.\n\nSaludos cordiales,\nClínica Veterinaria'
    }

    return jsonify({'settings': settings}), 200


# Proxy para guardar configuración general
@app.route('/api/admin/settings/general', methods=['PUT'])
@login_required
def admin_save_general_settings():
    """API para guardar configuración general"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Simulación de guardado
    return jsonify({'message': 'Configuración guardada exitosamente'}), 200


# Proxy para guardar configuración de notificaciones
@app.route('/api/admin/settings/notifications', methods=['PUT'])
@login_required
def admin_save_notification_settings():
    """API para guardar configuración de notificaciones"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Simulación de guardado
    return jsonify({'message': 'Configuración de notificaciones guardada exitosamente'}), 200


# Proxy para generar respaldo
@app.route('/api/admin/settings/backup')
@login_required
def admin_generate_backup():
    """API para generar respaldo de la base de datos"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Crear un archivo SQL simulado
    backup_content = "-- Backup simulado de la base de datos\n"
    backup_content += "-- Fecha: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
    backup_content += "-- Tablas y datos irían aquí en un respaldo real\n"

    # Crear una respuesta con el archivo SQL
    response = make_response(backup_content)
    response.headers["Content-Disposition"] = "attachment; filename=backup.sql"
    response.headers["Content-Type"] = "text/plain"

    return response


# Proxy para restaurar desde respaldo
@app.route('/api/admin/settings/restore', methods=['POST'])
@login_required
def admin_restore_from_backup():
    """API para restaurar desde respaldo"""
    user = session.get('user')

    # Verificar que el usuario sea administrador
    if user['role'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'}), 403

    # Verificar que se haya subido un archivo
    if 'backup_file' not in request.files:
        return jsonify({'error': 'No se ha proporcionado archivo de respaldo'}), 400

    # Simulación de restauración
    return jsonify({'message': 'Restauración completada exitosamente'}), 200


#
# DASHBOARDS ESPECÍFICOS POR ROL
#

@app.route('/dashboard/veterinarian')
@login_required
def vet_dashboard():
    """Dashboard específico para veterinarios"""
    user = session.get('user')

    # Verificar que el usuario sea veterinario
    if user['role'] != 'veterinarian':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('dashboard'))

    headers = {'Authorization': f'Bearer {session["token"]}'}

    # Obtener citas del día para este veterinario
    today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?veterinarian_id={user["id"]}&date_from={today}&date_to={today}',
        headers=headers
    )

    today_appointments = response.json().get('appointments', []) if response.status_code == 200 else []

    # Obtener todas las citas pendientes
    response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?veterinarian_id={user["id"]}&status=scheduled',
        headers=headers
    )

    upcoming_appointments = response.json().get('appointments', []) if response.status_code == 200 else []

    # Obtener horario del veterinario
    response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/schedules/staff-schedules/{user["id"]}',
        headers=headers
    )

    schedules = response.json().get('schedules', []) if response.status_code == 200 else []

    # Obtener notificaciones
    notif_response = requests.get(
        f'{NOTIFICATION_SERVICE_URL}/api/notifications/notifications/{user["id"]}?status=pending',
    )
    notifications = notif_response.json().get('notifications', []) if notif_response.status_code == 200 else []

    return render_template(
        'veterinarian_dashboard.html',
        user=user,
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments,
        schedules=schedules,
        notifications=notifications,
        today=today
    )


@app.route('/dashboard/receptionist')
@login_required
def receptionist_dashboard():
    """Dashboard específico para recepcionistas"""
    user = session.get('user')

    # Verificar que el usuario sea recepcionista
    if user['role'] != 'receptionist':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('dashboard'))

    headers = {'Authorization': f'Bearer {session["token"]}'}

    # Obtener citas del día
    today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?date_from={today}&date_to={today}',
        headers=headers
    )

    today_appointments = response.json().get('appointments', []) if response.status_code == 200 else []

    # Obtener lista de veterinarios disponibles hoy
    response = requests.get(f'{AUTH_SERVICE_URL}/api/auth/veterinarians', headers=headers)
    veterinarians = response.json().get('veterinarians', []) if response.status_code == 200 else []

    # Obtener notificaciones
    notif_response = requests.get(
        f'{NOTIFICATION_SERVICE_URL}/api/notifications/notifications/{user["id"]}?status=pending',
    )
    notifications = notif_response.json().get('notifications', []) if notif_response.status_code == 200 else []

    return render_template(
        'receptionist_dashboard.html',
        user=user,
        today_appointments=today_appointments,
        veterinarians=veterinarians,
        notifications=notifications,
        today=today
    )


@app.route('/dashboard/assistant')
@login_required
def assistant_dashboard():
    """Dashboard específico para auxiliares veterinarios"""
    user = session.get('user')

    # Verificar que el usuario sea auxiliar
    if user['role'] != 'assistant':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('dashboard'))

    headers = {'Authorization': f'Bearer {session["token"]}'}

    # Obtener citas del día
    today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(
        f'{APPOINTMENT_SERVICE_URL}/api/appointments/appointments?date_from={today}&date_to={today}',
        headers=headers
    )

    today_appointments = response.json().get('appointments', []) if response.status_code == 200 else []

    # Obtener lista de tareas pendientes (simulado, esto requeriría un nuevo servicio de tareas)
    tasks = [
        {
            'id': 1,
            'description': 'Preparar consultorio 1',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 2,
            'description': 'Revisar inventario de medicamentos',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 3,
            'description': 'Asistir al Dr. García con cirugía',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
    ]

    # Obtener notificaciones
    notif_response = requests.get(
        f'{NOTIFICATION_SERVICE_URL}/api/notifications/notifications/{user["id"]}?status=pending',
    )
    notifications = notif_response.json().get('notifications', []) if notif_response.status_code == 200 else []

    return render_template(
        'assistant_dashboard.html',
        user=user,
        today_appointments=today_appointments,
        tasks=tasks,
        notifications=notifications,
        today=today
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)