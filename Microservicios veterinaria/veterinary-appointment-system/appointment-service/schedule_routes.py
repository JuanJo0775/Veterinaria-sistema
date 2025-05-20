from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError, post_load
from datetime import datetime, time, timedelta
import requests
import os
from models import VeterinarianAvailability, Appointment, StaffSchedule
from db import db

schedule_bp = Blueprint('schedules', __name__)


# Schemas de validación
class ScheduleSchema(Schema):
    staff_id = fields.Int(required=True)
    day_of_week = fields.Int(required=True, validate=lambda x: 0 <= x <= 6)
    start_time = fields.Time(required=True)
    end_time = fields.Time(required=True)
    break_start = fields.Time(required=False, allow_none=True)
    break_end = fields.Time(required=False, allow_none=True)
    max_appointments = fields.Int(required=False, load_default=8)  # Usar missing en lugar de default
    appointment_duration = fields.Int(required=False, load_default=30)  # Usar missing en lugar de default
    is_available = fields.Bool(required=False, load_default=True)  # Usar missing en lugar de default

    @post_load
    def set_defaults(self, data, **kwargs):
        # Establecer valores predeterminados si no existen
        if 'max_appointments' not in data:
            data['max_appointments'] = 8
        if 'appointment_duration' not in data:
            data['appointment_duration'] = 30
        if 'is_available' not in data:
            data['is_available'] = True
        return data

# Instancias de schemas
schedule_schema = ScheduleSchema()


# Función para verificar token con el servicio de autenticación
def verify_token(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{os.getenv('AUTH_SERVICE_URL')}/api/auth/verify-token", headers=headers)
    return response.status_code == 200


# Función para verificar si el usuario es un administrador
def verify_admin(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{os.getenv('AUTH_SERVICE_URL')}/api/auth/me", headers=headers)
    if response.status_code != 200:
        return False

    user_data = response.json().get('user', {})
    return user_data.get('role') == 'admin'


# Middleware para verificar autenticación y permisos de administrador
def admin_required(f):
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_token(token) or not verify_admin(token):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Rutas para gestión de horarios
@schedule_bp.route('/staff-schedules', methods=['POST'])
@admin_required
def create_staff_schedule():
    try:
        data = schedule_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verificar que las horas sean coherentes
    if data['start_time'] >= data['end_time']:
        return jsonify({'error': 'Start time must be before end time'}), 400

    # Verificar horario de descanso si se proporciona
    if data.get('break_start') and data.get('break_end'):
        if data['break_start'] >= data['break_end']:
            return jsonify({'error': 'Break start time must be before break end time'}), 400
        if data['break_start'] < data['start_time'] or data['break_end'] > data['end_time']:
            return jsonify({'error': 'Break time must be within work hours'}), 400

    # Verificar si ya existe un horario para ese día
    existing_schedule = StaffSchedule.query.filter_by(
        staff_id=data['staff_id'],
        day_of_week=data['day_of_week']
    ).first()

    if existing_schedule:
        # Actualizar el horario existente
        for key, value in data.items():
            setattr(existing_schedule, key, value)

        try:
            db.session.commit()
            return jsonify({
                'message': 'Schedule updated successfully',
                'schedule': existing_schedule.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Error updating schedule', 'message': str(e)}), 500

    # Crear nuevo horario
    schedule = StaffSchedule(**data)

    try:
        db.session.add(schedule)
        db.session.commit()
        return jsonify({
            'message': 'Schedule created successfully',
            'schedule': schedule.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating schedule', 'message': str(e)}), 500


@schedule_bp.route('/staff-schedules/<int:staff_id>', methods=['GET'])
def get_staff_schedules(staff_id):
    schedules = StaffSchedule.query.filter_by(staff_id=staff_id).all()
    return jsonify({
        'schedules': [schedule.to_dict() for schedule in schedules]
    }), 200


@schedule_bp.route('/staff-schedules/<int:schedule_id>', methods=['PUT'])
@admin_required
def update_staff_schedule(schedule_id):
    schedule = StaffSchedule.query.get(schedule_id)

    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404

    try:
        data = schedule_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verificar que las horas sean coherentes si se están actualizando
    if 'start_time' in data and 'end_time' in data:
        if data['start_time'] >= data['end_time']:
            return jsonify({'error': 'Start time must be before end time'}), 400
    elif 'start_time' in data and schedule.end_time:
        if data['start_time'] >= schedule.end_time:
            return jsonify({'error': 'Start time must be before end time'}), 400
    elif 'end_time' in data and schedule.start_time:
        if schedule.start_time >= data['end_time']:
            return jsonify({'error': 'Start time must be before end time'}), 400

    # Actualizar campos
    for key, value in data.items():
        setattr(schedule, key, value)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Schedule updated successfully',
            'schedule': schedule.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating schedule', 'message': str(e)}), 500


@schedule_bp.route('/staff-schedules/<int:schedule_id>', methods=['DELETE'])
@admin_required
def delete_staff_schedule(schedule_id):
    schedule = StaffSchedule.query.get(schedule_id)

    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404

    try:
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({'message': 'Schedule deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error deleting schedule', 'message': str(e)}), 500


@schedule_bp.route('/staff-schedules/copy', methods=['POST'])
@admin_required
def copy_staff_schedule():
    # Copiar un horario de un empleado a otro o a todos los de un rol
    source_id = request.json.get('source_staff_id')
    target_ids = request.json.get('target_staff_ids', [])
    target_role = request.json.get('target_role')

    if not source_id:
        return jsonify({'error': 'Source staff ID is required'}), 400

    if not target_ids and not target_role:
        return jsonify({'error': 'Either target staff IDs or target role is required'}), 400

    # Obtener los horarios de origen
    source_schedules = StaffSchedule.query.filter_by(staff_id=source_id).all()

    if not source_schedules:
        return jsonify({'error': 'No schedules found for source staff member'}), 404

    # Si se especifica un rol objetivo, obtener IDs de los empleados con ese rol
    if target_role:
        response = requests.get(f"{os.getenv('AUTH_SERVICE_URL')}/api/admin/staff?role={target_role}")
        if response.status_code != 200:
            return jsonify({'error': 'Error fetching staff by role'}), 500

        staff_data = response.json().get('staff', [])
        target_ids = [staff['id'] for staff in staff_data if staff['id'] != source_id]

    success_count = 0
    error_count = 0

    # Copiar horarios a cada empleado objetivo
    for target_id in target_ids:
        for source_schedule in source_schedules:
            # Verificar si ya existe un horario para ese día
            existing_schedule = StaffSchedule.query.filter_by(
                staff_id=target_id,
                day_of_week=source_schedule.day_of_week
            ).first()

            if existing_schedule:
                # Actualizar el horario existente
                existing_schedule.start_time = source_schedule.start_time
                existing_schedule.end_time = source_schedule.end_time
                existing_schedule.break_start = source_schedule.break_start
                existing_schedule.break_end = source_schedule.break_end
                existing_schedule.max_appointments = source_schedule.max_appointments
                existing_schedule.appointment_duration = source_schedule.appointment_duration
                existing_schedule.is_available = source_schedule.is_available
            else:
                # Crear nuevo horario
                new_schedule = StaffSchedule(
                    staff_id=target_id,
                    day_of_week=source_schedule.day_of_week,
                    start_time=source_schedule.start_time,
                    end_time=source_schedule.end_time,
                    break_start=source_schedule.break_start,
                    break_end=source_schedule.break_end,
                    max_appointments=source_schedule.max_appointments,
                    appointment_duration=source_schedule.appointment_duration,
                    is_available=source_schedule.is_available
                )
                db.session.add(new_schedule)

            try:
                db.session.commit()
                success_count += 1
            except Exception as e:
                db.session.rollback()
                error_count += 1

    return jsonify({
        'message': f'Copied schedules: {success_count} successful, {error_count} failed',
        'success_count': success_count,
        'error_count': error_count
    }), 200 if success_count > 0 else 500