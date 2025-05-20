# appointment-service/routes.py
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, date, time, timedelta
import requests
import os
from models import Appointment, Pet, VeterinarianAvailability
from db import db  # Importar desde db.py



appointment_bp = Blueprint('appointments', __name__)


# Schemas de validación
class AppointmentSchema(Schema):
    client_id = fields.Int(required=True)
    veterinarian_id = fields.Int(required=True)
    pet_id = fields.Int(required=True)
    appointment_date = fields.Date(required=True)
    appointment_time = fields.Time(required=True)
    duration_minutes = fields.Int(load_default=30)
    reason = fields.Str(required=True)
    notes = fields.Str()


class PetSchema(Schema):
    owner_id = fields.Int(required=True)
    name = fields.Str(required=True)
    species = fields.Str(required=True)
    breed = fields.Str()
    age = fields.Int()
    weight = fields.Float()


# Instancias de schemas
appointment_schema = AppointmentSchema()
pet_schema = PetSchema()


# Función para verificar token con el servicio de autenticación
def verify_token(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{os.getenv('AUTH_SERVICE_URL')}/api/auth/verify-token", headers=headers)
    return response.status_code == 200


# Middleware para verificar autenticación
def require_auth(f):
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_token(token):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Rutas para citas
@appointment_bp.route('/appointments', methods=['POST'])
@require_auth
def create_appointment():
    try:
        data = appointment_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verificar disponibilidad del veterinario
    appointment_date = data['appointment_date']
    appointment_time = data['appointment_time']

    # Obtener el día de la semana (0 = Lunes, 6 = Domingo)
    day_of_week = appointment_date.weekday()

    # Verificar si el veterinario trabaja ese día
    availability = VeterinarianAvailability.query.filter_by(
        veterinarian_id=data['veterinarian_id'],
        day_of_week=day_of_week,
        is_available=True
    ).first()

    if not availability:
        return jsonify({'error': 'Veterinarian not available on this day'}), 400

    # Verificar si el horario está dentro de las horas de trabajo
    if appointment_time < availability.start_time or appointment_time >= availability.end_time:
        return jsonify({'error': 'Appointment time outside working hours'}), 400

    # Verificar si no hay conflicto con otra cita
    existing_appointment = Appointment.query.filter_by(
        veterinarian_id=data['veterinarian_id'],
        appointment_date=appointment_date,
        appointment_time=appointment_time
    ).first()

    if existing_appointment:
        return jsonify({'error': 'Time slot already booked'}), 409

    # Crear la cita
    appointment = Appointment(**data)

    try:
        db.session.add(appointment)
        db.session.commit()
        return jsonify({
            'message': 'Appointment created successfully',
            'appointment': appointment.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating appointment', 'message': str(e)}), 500


@appointment_bp.route('/appointments', methods=['GET'])
@require_auth
def get_appointments():
    # Filtros opcionales
    client_id = request.args.get('client_id', type=int)
    veterinarian_id = request.args.get('veterinarian_id', type=int)
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = Appointment.query

    if client_id:
        query = query.filter_by(client_id=client_id)
    if veterinarian_id:
        query = query.filter_by(veterinarian_id=veterinarian_id)
    if status:
        query = query.filter_by(status=status)
    if date_from:
        query = query.filter(Appointment.appointment_date >= date_from)
    if date_to:
        query = query.filter(Appointment.appointment_date <= date_to)

    appointments = query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    return jsonify({
        'appointments': [appointment.to_dict() for appointment in appointments]
    }), 200


@appointment_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@require_auth
def get_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    return jsonify({'appointment': appointment.to_dict()}), 200


@appointment_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@require_auth
def update_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    data = request.json

    # Actualizar los campos permitidos
    if 'status' in data:
        appointment.status = data['status']
    if 'notes' in data:
        appointment.notes = data['notes']
    if 'reason' in data:
        appointment.reason = data['reason']

    try:
        db.session.commit()
        return jsonify({
            'message': 'Appointment updated successfully',
            'appointment': appointment.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating appointment', 'message': str(e)}), 500


@appointment_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@require_auth
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    appointment.status = 'cancelled'

    try:
        db.session.commit()
        return jsonify({'message': 'Appointment cancelled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error cancelling appointment', 'message': str(e)}), 500


# Rutas para mascotas
@appointment_bp.route('/pets', methods=['POST'])
@require_auth
def create_pet():
    try:
        data = pet_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    pet = Pet(**data)

    try:
        db.session.add(pet)
        db.session.commit()
        return jsonify({
            'message': 'Pet created successfully',
            'pet': pet.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating pet', 'message': str(e)}), 500


@appointment_bp.route('/pets/<int:owner_id>', methods=['GET'])
@require_auth
def get_owner_pets(owner_id):
    pets = Pet.query.filter_by(owner_id=owner_id).all()
    return jsonify({
        'pets': [pet.to_dict() for pet in pets]
    }), 200


# Rutas para disponibilidad
@appointment_bp.route('/availability/<int:veterinarian_id>', methods=['GET'])
def get_veterinarian_availability(veterinarian_id):
    availability = VeterinarianAvailability.query.filter_by(
        veterinarian_id=veterinarian_id,
        is_available=True
    ).all()

    return jsonify({
        'availability': [avail.to_dict() for avail in availability]
    }), 200


@appointment_bp.route('/available-slots/<int:veterinarian_id>', methods=['GET'])
def get_available_slots(veterinarian_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400

    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_of_week = appointment_date.weekday()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Obtener disponibilidad del veterinario para ese día
    availability = VeterinarianAvailability.query.filter_by(
        veterinarian_id=veterinarian_id,
        day_of_week=day_of_week,
        is_available=True
    ).first()

    if not availability:
        return jsonify({'available_slots': []}), 200

    # Obtener citas existentes para ese día
    existing_appointments = Appointment.query.filter_by(
        veterinarian_id=veterinarian_id,
        appointment_date=appointment_date
    ).filter(Appointment.status != 'cancelled').all()

    booked_times = [appt.appointment_time for appt in existing_appointments]

    # Generar slots disponibles
    available_slots = []
    current_time = availability.start_time
    slot_duration = timedelta(minutes=30)

    while current_time < availability.end_time:
        if current_time not in booked_times:
            available_slots.append(current_time.strftime('%H:%M'))
        current_time = (datetime.combine(date.today(), current_time) + slot_duration).time()

    return jsonify({'available_slots': available_slots}), 200


@appointment_bp.route('/appointments/stats', methods=['GET'])
def get_appointment_stats():
    """Obtener estadísticas de citas para el panel de administración"""
    # Parámetros opcionales
    date_str = request.args.get('date')

    # Obtener la fecha actual si no se proporciona
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        target_date = datetime.now().date()

    # Estadísticas para el día actual
    today_appointments = Appointment.query.filter_by(appointment_date=target_date).count()

    # Estadísticas por estado
    scheduled_count = Appointment.query.filter_by(status='scheduled').count()
    completed_count = Appointment.query.filter_by(status='completed').count()
    cancelled_count = Appointment.query.filter_by(status='cancelled').count()
    no_show_count = Appointment.query.filter_by(status='no-show').count()

    # Estadísticas por veterinario
    vet_stats_query = db.session.query(
        Appointment.veterinarian_id,
        db.func.count(Appointment.id)
    ).group_by(Appointment.veterinarian_id).all()

    vet_stats = {vet_id: count for vet_id, count in vet_stats_query}

    # Estadísticas por mes (para el año actual)
    current_year = datetime.now().year
    monthly_stats_query = db.session.query(
        db.extract('month', Appointment.appointment_date),
        db.func.count(Appointment.id)
    ).filter(
        db.extract('year', Appointment.appointment_date) == current_year
    ).group_by(
        db.extract('month', Appointment.appointment_date)
    ).all()

    monthly_stats = {int(month): count for month, count in monthly_stats_query}

    return jsonify({
        'appointment_stats': {
            'today': today_appointments,
            'scheduled': scheduled_count,
            'completed': completed_count,
            'cancelled': cancelled_count,
            'no_show': no_show_count,
            'by_veterinarian': vet_stats,
            'monthly': monthly_stats
        }
    }), 200