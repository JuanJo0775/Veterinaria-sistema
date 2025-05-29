#!/usr/bin/env python3
# run_appointment_service.py
# Appointment Service simplificado

import os
import sys
from pathlib import Path

# Configurar paths
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "utils"))

# Configurar variables de entorno
env_vars = {
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_DB': 'veterinary-system',
    'POSTGRES_USER': 'postgres',
    'POSTGRES_PASSWORD': 'bocato0731',
    'REDIS_URL': 'redis://localhost:6379/1',
    'FLASK_ENV': 'development',
    'SECRET_KEY': 'dev-secret-key-appointment',
    'AUTH_SERVICE_URL': 'http://localhost:5001',
    'NOTIFICATION_SERVICE_URL': 'http://localhost:5003',
    'MEDICAL_SERVICE_URL': 'http://localhost:5004'
}

for key, value in env_vars.items():
    os.environ.setdefault(key, value)


def create_appointment_app():
    """Crear la aplicación de Citas"""
    from flask import Flask, Blueprint, request, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_cors import CORS
    from datetime import datetime, timedelta, time, date
    import uuid
    import requests

    # Crear app
    app = Flask(__name__)

    # Configuración
    app.config.update({
        'SECRET_KEY': os.environ['SECRET_KEY'],
        'SQLALCHEMY_DATABASE_URI': (
            f"postgresql://{os.environ['POSTGRES_USER']}:"
            f"{os.environ['POSTGRES_PASSWORD']}@"
            f"{os.environ['POSTGRES_HOST']}:5432/"
            f"{os.environ['POSTGRES_DB']}"
        ),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': True
    })

    # Inicializar extensiones
    db = SQLAlchemy(app)
    CORS(app)

    # Modelo Appointment
    class Appointment(db.Model):
        __tablename__ = 'appointments'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        pet_id = db.Column(db.String(36), nullable=False)
        veterinarian_id = db.Column(db.String(36), nullable=False)
        client_id = db.Column(db.String(36), nullable=False)
        appointment_date = db.Column(db.Date, nullable=False)
        appointment_time = db.Column(db.Time, nullable=False)
        status = db.Column(db.Enum('scheduled', 'confirmed', 'completed', 'cancelled', name='appointment_status_enum'),
                           default='scheduled')
        reason = db.Column(db.Text)
        notes = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return {
                'id': self.id,
                'pet_id': self.pet_id,
                'veterinarian_id': self.veterinarian_id,
                'client_id': self.client_id,
                'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
                'appointment_time': self.appointment_time.strftime('%H:%M') if self.appointment_time else None,
                'status': self.status,
                'reason': self.reason,
                'notes': self.notes,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

        @classmethod
        def check_availability(cls, vet_id, appointment_date, appointment_time):
            existing = cls.query.filter_by(
                veterinarian_id=vet_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='scheduled'
            ).first()
            return existing is None

    # Modelo VeterinarianSchedule
    class VeterinarianSchedule(db.Model):
        __tablename__ = 'veterinarian_schedules'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        veterinarian_id = db.Column(db.String(36), nullable=False)
        day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes, 6=Domingo
        start_time = db.Column(db.Time, nullable=False)
        end_time = db.Column(db.Time, nullable=False)
        is_available = db.Column(db.Boolean, default=True)

        def to_dict(self):
            return {
                'id': self.id,
                'veterinarian_id': self.veterinarian_id,
                'day_of_week': self.day_of_week,
                'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
                'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
                'is_available': self.is_available
            }

    # Servicios
    class AppointmentService:
        @staticmethod
        def check_availability(veterinarian_id, appointment_date, appointment_time):
            if isinstance(appointment_date, str):
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            if isinstance(appointment_time, str):
                appointment_time = datetime.strptime(appointment_time, '%H:%M').time()

            day_of_week = appointment_date.weekday()
            schedule = VeterinarianSchedule.query.filter_by(
                veterinarian_id=veterinarian_id,
                day_of_week=day_of_week,
                is_available=True
            ).first()

            if not schedule or not (schedule.start_time <= appointment_time <= schedule.end_time):
                return False

            return Appointment.check_availability(veterinarian_id, appointment_date, appointment_time)

        @staticmethod
        def create_appointment(appointment_data):
            appointment = Appointment(
                pet_id=appointment_data.get('pet_id'),
                veterinarian_id=appointment_data.get('veterinarian_id'),
                client_id=appointment_data.get('client_id'),
                appointment_date=datetime.strptime(appointment_data.get('appointment_date'), '%Y-%m-%d').date(),
                appointment_time=datetime.strptime(appointment_data.get('appointment_time'), '%H:%M').time(),
                reason=appointment_data.get('reason'),
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            return appointment

        @staticmethod
        def get_available_slots(veterinarian_id, date_str):
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            day_of_week = appointment_date.weekday()

            schedule = VeterinarianSchedule.query.filter_by(
                veterinarian_id=veterinarian_id,
                day_of_week=day_of_week,
                is_available=True
            ).first()

            if not schedule:
                return []

            slots = []
            current_time = schedule.start_time
            end_time = schedule.end_time

            while current_time < end_time:
                if Appointment.check_availability(veterinarian_id, appointment_date, current_time):
                    slots.append(current_time.strftime('%H:%M'))

                current_datetime = datetime.combine(appointment_date, current_time)
                current_datetime += timedelta(minutes=30)
                current_time = current_datetime.time()

            return slots

    # Rutas
    appointment_bp = Blueprint('appointments', __name__)
    appointment_service = AppointmentService()

    @appointment_bp.route('/create', methods=['POST'])
    def create_appointment():
        try:
            data = request.get_json()

            required_fields = ['pet_id', 'veterinarian_id', 'client_id', 'appointment_date', 'appointment_time']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            if not appointment_service.check_availability(
                    data.get('veterinarian_id'),
                    data.get('appointment_date'),
                    data.get('appointment_time')
            ):
                return jsonify({'success': False, 'message': 'Horario no disponible'}), 400

            appointment = appointment_service.create_appointment(data)

            return jsonify({
                'success': True,
                'appointment_id': appointment.id,
                'message': 'Cita creada exitosamente',
                'appointment': appointment.to_dict()
            }), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @appointment_bp.route('/available-slots', methods=['GET'])
    def get_available_slots():
        try:
            veterinarian_id = request.args.get('veterinarian_id')
            date = request.args.get('date')

            if not veterinarian_id or not date:
                return jsonify({'success': False, 'message': 'Parámetros requeridos: veterinarian_id, date'}), 400

            slots = appointment_service.get_available_slots(veterinarian_id, date)

            return jsonify({
                'success': True,
                'available_slots': slots,
                'date': date,
                'veterinarian_id': veterinarian_id
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @appointment_bp.route('/by-veterinarian/<vet_id>', methods=['GET'])
    def get_appointments_by_vet(vet_id):
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            query = Appointment.query.filter_by(veterinarian_id=vet_id)
            if start_date:
                query = query.filter(Appointment.appointment_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(Appointment.appointment_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

            appointments = query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()

            return jsonify({
                'success': True,
                'appointments': [apt.to_dict() for apt in appointments],
                'veterinarian_id': vet_id
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @appointment_bp.route('/today', methods=['GET'])
    def get_today_appointments():
        try:
            today = datetime.now().date()
            appointments = Appointment.query.filter(
                Appointment.appointment_date == today,
                Appointment.status.in_(['scheduled', 'confirmed'])
            ).order_by(Appointment.appointment_time).all()

            return jsonify({
                'success': True,
                'appointments': [apt.to_dict() for apt in appointments],
                'date': today.isoformat()
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # Health check
    @app.route('/health')
    def health():
        try:
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'service': 'appointment_service',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'appointment_service',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    # Registrar blueprint
    app.register_blueprint(appointment_bp, url_prefix='/appointments')

    # Crear tablas
    with app.app_context():
        db.create_all()
        print("✅ Tablas de appointment service creadas/verificadas")

    return app


def main():
    print("🚀 Iniciando Appointment Service...")
    print(f"📂 Directorio: {ROOT_DIR}")
    print("🔧 Variables de entorno configuradas")

    try:
        app = create_appointment_app()

        print("🎯 Configuración completada!")
        print("🌐 URLs disponibles:")
        print("   - Health Check: http://localhost:5002/health")
        print("   - Create Appointment: http://localhost:5002/appointments/create")
        print("   - Available Slots: http://localhost:5002/appointments/available-slots")
        print("   - Today's Appointments: http://localhost:5002/appointments/today")
        print("")
        print("🚀 Appointment Service iniciado en http://localhost:5002")
        print("💡 Presiona Ctrl+C para detener el servicio")
        print("=" * 60)

        app.run(host='0.0.0.0', port=5002, debug=True)

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()