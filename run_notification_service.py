#!/usr/bin/env python3
# run_notification_service.py
# Notification Service simplificado

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
    'REDIS_URL': 'redis://localhost:6379/2',
    'FLASK_ENV': 'development',
    'SECRET_KEY': 'dev-secret-key-notification',
    'GMAIL_USER': 'dev@veterinariaclinic.com',
    'GMAIL_PASSWORD': 'dev_password',
    'TWILIO_ACCOUNT_SID': 'dev_account_sid',
    'TWILIO_AUTH_TOKEN': 'dev_auth_token',
    'TWILIO_PHONE_NUMBER': '+1234567890',
    'AUTH_SERVICE_URL': 'http://localhost:5001',
    'APPOINTMENT_SERVICE_URL': 'http://localhost:5002',
    'MEDICAL_SERVICE_URL': 'http://localhost:5004',
    'INVENTORY_SERVICE_URL': 'http://localhost:5005'
}

for key, value in env_vars.items():
    os.environ.setdefault(key, value)


def create_notification_app():
    """Crear la aplicación Notification Service"""
    from flask import Flask, Blueprint, request, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_cors import CORS
    from datetime import datetime
    import uuid
    import logging

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

    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Modelo Notification
    class Notification(db.Model):
        __tablename__ = 'notifications'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = db.Column(db.String(36), nullable=False)
        type = db.Column(db.Enum('appointment_reminder', 'new_appointment', 'inventory_alert', 'general',
                                 name='notification_type_enum'), nullable=False)
        title = db.Column(db.String(255), nullable=False)
        message = db.Column(db.Text, nullable=False)
        is_read = db.Column(db.Boolean, default=False)
        sent_at = db.Column(db.DateTime)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        email_sent = db.Column(db.Boolean, default=False)
        sms_sent = db.Column(db.Boolean, default=False)
        email_sent_at = db.Column(db.DateTime)
        sms_sent_at = db.Column(db.DateTime)

        def to_dict(self):
            return {
                'id': self.id,
                'user_id': self.user_id,
                'type': self.type,
                'title': self.title,
                'message': self.message,
                'is_read': self.is_read,
                'email_sent': self.email_sent,
                'sms_sent': self.sms_sent,
                'sent_at': self.sent_at.isoformat() if self.sent_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

        @classmethod
        def create_notification(cls, user_id, notification_type, title, message):
            notification = cls(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message
            )
            db.session.add(notification)
            db.session.commit()
            return notification

    # Servicios de notificación simulados
    class EmailService:
        @staticmethod
        def send_email(to_email, subject, body, html_body=None):
            if os.environ['FLASK_ENV'] == 'development':
                logger.info(f"📧 [SIMULADO] Email enviado a {to_email}")
                logger.info(f"   Asunto: {subject}")
                logger.info(f"   Contenido: {body[:100]}...")
                return True
            return False

        @staticmethod
        def send_appointment_reminder(to_email, appointment_details):
            subject = "🐾 Recordatorio de Cita - Clínica Veterinaria"
            body = f"""
Estimado cliente,

Le recordamos que tiene una cita programada:

📅 Fecha: {appointment_details.get('date')}
🕐 Hora: {appointment_details.get('time')}
👨‍⚕️ Veterinario: Dr. {appointment_details.get('veterinarian_name', 'N/A')}
🐕 Mascota: {appointment_details.get('pet_name', 'N/A')}
📋 Motivo: {appointment_details.get('reason', 'Consulta general')}

Por favor, llegue 15 minutos antes de su cita.

Saludos cordiales,
Clínica Veterinaria
            """
            return EmailService.send_email(to_email, subject, body)

        @staticmethod
        def send_new_appointment_alert(to_email, appointment_details):
            subject = "🔔 Nueva Cita Agendada - Clínica Veterinaria"
            body = f"""
Nueva cita agendada en el sistema:

📅 Fecha: {appointment_details.get('date')}
🕐 Hora: {appointment_details.get('time')}
👨‍⚕️ Veterinario: Dr. {appointment_details.get('veterinarian_name', 'N/A')}
👤 Cliente: {appointment_details.get('client_name', 'N/A')}
🐕 Mascota: {appointment_details.get('pet_name', 'N/A')}
📋 Motivo: {appointment_details.get('reason', 'Consulta general')}

Por favor, revise la agenda y confirme con el cliente si es necesario.
            """
            return EmailService.send_email(to_email, subject, body)

        @staticmethod
        def send_inventory_alert(to_email, medication_details, alert_type):
            if alert_type == 'low_stock':
                subject = "⚠️ Alerta de Stock Bajo - Clínica Veterinaria"
                if isinstance(medication_details, list):
                    medications_list = "\n".join(
                        [f"• {med.get('name', 'N/A')} - Stock: {med.get('stock_quantity', 0)} unidades" for med in
                         medication_details])
                else:
                    medications_list = f"• {medication_details.get('name', 'N/A')} - Stock: {medication_details.get('stock_quantity', 0)} unidades"

                body = f"""
ALERTA: Los siguientes medicamentos tienen stock bajo:

{medications_list}

Por favor, proceder con el reabastecimiento lo antes posible.
                """
            else:  # expiration
                subject = "⚠️ Alerta de Medicamentos por Vencer - Clínica Veterinaria"
                if isinstance(medication_details, list):
                    medications_list = "\n".join(
                        [f"• {med.get('name', 'N/A')} - Vence: {med.get('expiration_date', 'N/A')}" for med in
                         medication_details])
                else:
                    medications_list = f"• {medication_details.get('name', 'N/A')} - Vence: {medication_details.get('expiration_date', 'N/A')}"

                body = f"""
ALERTA: Los siguientes medicamentos están próximos a vencer:

{medications_list}

Por favor, revisar y tomar las medidas necesarias.
                """

            return EmailService.send_email(to_email, subject, body)

    class WhatsAppService:
        @staticmethod
        def send_whatsapp_message(to_phone, message):
            if os.environ['FLASK_ENV'] == 'development':
                logger.info(f"📱 [SIMULADO] WhatsApp enviado a {to_phone}")
                logger.info(f"   Mensaje: {message[:100]}...")
                return True
            return False

        @staticmethod
        def send_appointment_reminder(to_phone, appointment_details):
            message = f"""
🐾 *Recordatorio de Cita*

Hola! Le recordamos su cita:

📅 *Fecha:* {appointment_details.get('date')}
🕐 *Hora:* {appointment_details.get('time')}
👨‍⚕️ *Veterinario:* Dr. {appointment_details.get('veterinarian_name', 'N/A')}
🐕 *Mascota:* {appointment_details.get('pet_name', 'N/A')}

Por favor llegue 15 minutos antes.

_Clínica Veterinaria_
📞 +1234567890
            """.strip()
            return WhatsAppService.send_whatsapp_message(to_phone, message)

    # Rutas
    notification_bp = Blueprint('notifications', __name__)
    email_service = EmailService()
    whatsapp_service = WhatsAppService()

    @notification_bp.route('/send-reminder', methods=['POST'])
    def send_appointment_reminder():
        try:
            data = request.get_json()

            required_fields = ['user_id', 'appointment_details']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            appointment_details = data.get('appointment_details')
            user_id = data.get('user_id')
            email = data.get('email')
            phone = data.get('phone')

            results = {'email_sent': False, 'whatsapp_sent': False}

            if email:
                results['email_sent'] = email_service.send_appointment_reminder(email, appointment_details)

            if phone:
                results['whatsapp_sent'] = whatsapp_service.send_appointment_reminder(phone, appointment_details)

            # Guardar notificación
            notification = Notification.create_notification(
                user_id=user_id,
                notification_type='appointment_reminder',
                title='Recordatorio de Cita',
                message=f"Recordatorio: Cita programada para {appointment_details.get('date')} a las {appointment_details.get('time')}"
            )

            notification.email_sent = results['email_sent']
            notification.sms_sent = results['whatsapp_sent']
            notification.sent_at = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'notification_id': notification.id,
                'email_sent': results['email_sent'],
                'whatsapp_sent': results['whatsapp_sent']
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @notification_bp.route('/appointment-alert', methods=['POST'])
    def send_appointment_alert():
        try:
            data = request.get_json()

            appointment_details = data.get('appointment_details')
            receptionist_emails = data.get('receptionist_emails', [])

            if not appointment_details:
                return jsonify({'success': False, 'message': 'appointment_details requerido'}), 400

            emails_sent = 0
            for email in receptionist_emails:
                if email_service.send_new_appointment_alert(email, appointment_details):
                    emails_sent += 1

            return jsonify({
                'success': True,
                'message': f'Alertas enviadas a {emails_sent} recepcionistas',
                'emails_sent': emails_sent,
                'total_emails': len(receptionist_emails)
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @notification_bp.route('/inventory-alert', methods=['POST'])
    def send_inventory_alert():
        try:
            data = request.get_json()

            admin_emails = data.get('admin_emails', [])
            alert_type = data.get('alert_type')
            medication_details = data.get('medication_details')

            if not alert_type or not medication_details:
                return jsonify({'success': False, 'message': 'alert_type y medication_details requeridos'}), 400

            emails_sent = 0
            for email in admin_emails:
                if email_service.send_inventory_alert(email, medication_details, alert_type):
                    emails_sent += 1

            return jsonify({
                'success': True,
                'message': f'Alertas de inventario enviadas a {emails_sent} administradores',
                'emails_sent': emails_sent,
                'alert_type': alert_type
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @notification_bp.route('/test-email', methods=['POST'])
    def test_email():
        try:
            data = request.get_json()
            email = data.get('email')

            if not email:
                return jsonify({'success': False, 'message': 'email requerido'}), 400

            success = email_service.send_email(
                email,
                "Test Email - Clínica Veterinaria",
                "Este es un email de prueba del sistema de notificaciones."
            )

            return jsonify({'success': True, 'email_sent': success}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @notification_bp.route('/test-whatsapp', methods=['POST'])
    def test_whatsapp():
        try:
            data = request.get_json()
            phone = data.get('phone')

            if not phone:
                return jsonify({'success': False, 'message': 'phone requerido'}), 400

            success = whatsapp_service.send_whatsapp_message(
                phone,
                "🐾 Este es un mensaje de prueba del sistema de notificaciones de la Clínica Veterinaria."
            )

            return jsonify({'success': True, 'whatsapp_sent': success}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # Health check
    @app.route('/health')
    def health():
        try:
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'service': 'notification_service',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'notification_service',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    # Registrar blueprint
    app.register_blueprint(notification_bp, url_prefix='/notifications')

    # Crear tablas
    with app.app_context():
        db.create_all()
        print("✅ Tablas de notification service creadas/verificadas")

    return app


def main():
    print("🚀 Iniciando Notification Service...")
    print(f"📂 Directorio: {ROOT_DIR}")
    print("🔧 Variables de entorno configuradas")

    try:
        app = create_notification_app()

        print("🎯 Configuración completada!")
        print("🌐 URLs disponibles:")
        print("   - Health Check: http://localhost:5003/health")
        print("   - Send Reminder: http://localhost:5003/notifications/send-reminder")
        print("   - Appointment Alert: http://localhost:5003/notifications/appointment-alert")
        print("   - Inventory Alert: http://localhost:5003/notifications/inventory-alert")
        print("   - Test Email: http://localhost:5003/notifications/test-email")
        print("   - Test WhatsApp: http://localhost:5003/notifications/test-whatsapp")
        print("")
        print("🚀 Notification Service iniciado en http://localhost:5003")
        print("💡 Presiona Ctrl+C para detener el servicio")
        print("=" * 60)

        app.run(host='0.0.0.0', port=5003, debug=True)

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()