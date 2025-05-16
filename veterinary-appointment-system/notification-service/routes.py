# notification-service/routes.py
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, timedelta
from email_service import EmailService, db  # Importar db desde email_service

notification_bp = Blueprint('notifications', __name__)


# Modelos simples para notificaciones
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    appointment_id = db.Column(db.Integer)
    type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'appointment_id': self.appointment_id,
            'type': self.type,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Schemas de validación
class NotificationSchema(Schema):
    type = fields.Str(required=True, validate=lambda x: x in ['appointment_confirmation', 'appointment_reminder',
                                                              'appointment_cancellation', 'new_appointment'])
    recipient_email = fields.Email(required=True)
    appointment_details = fields.Dict(required=True)


class WebNotificationSchema(Schema):
    user_id = fields.Int(required=True)
    message = fields.Str(required=True)
    subject = fields.Str(required=True)


# Instancias de schemas
notification_schema = NotificationSchema()
web_notification_schema = WebNotificationSchema()


@notification_bp.route('/send-email', methods=['POST'])
def send_email_notification():
    try:
        data = notification_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    email_type = data['type']
    recipient_email = data['recipient_email']
    appointment_details = data['appointment_details']

    # Enviar el email según el tipo
    if email_type == 'appointment_confirmation':
        success, message = EmailService.send_appointment_confirmation(recipient_email, appointment_details)
    elif email_type == 'appointment_reminder':
        success, message = EmailService.send_appointment_reminder(recipient_email, appointment_details)
    elif email_type == 'appointment_cancellation':
        success, message = EmailService.send_appointment_cancellation(recipient_email, appointment_details)
    elif email_type == 'new_appointment':
        success, message = EmailService.send_vet_new_appointment(recipient_email, appointment_details)
    else:
        return jsonify({'error': 'Invalid notification type'}), 400

    # Registrar la notificación en la base de datos
    notification = Notification(
        user_id=appointment_details.get('user_id', 0),
        appointment_id=appointment_details.get('appointment_id'),
        type='email',
        subject=f"{email_type.replace('_', ' ').title()}",
        message=message,
        status='sent' if success else 'failed',
        sent_at=datetime.utcnow() if success else None
    )

    try:
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error saving notification', 'message': str(e)}), 500

    if success:
        return jsonify({'message': message, 'notification_id': notification.id}), 200
    else:
        return jsonify({'error': 'Failed to send email', 'message': message}), 500


@notification_bp.route('/web-notification', methods=['POST'])
def create_web_notification():
    try:
        data = web_notification_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    notification = Notification(
        user_id=data['user_id'],
        type='web',
        subject=data['subject'],
        message=data['message'],
        status='pending'
    )

    try:
        db.session.add(notification)
        db.session.commit()
        return jsonify({
            'message': 'Web notification created',
            'notification': notification.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating notification', 'message': str(e)}), 500


@notification_bp.route('/notifications/<int:user_id>', methods=['GET'])
def get_user_notifications(user_id):
    # Filtros opcionales
    status = request.args.get('status')
    type_filter = request.args.get('type')
    limit = request.args.get('limit', 50, type=int)

    query = Notification.query.filter_by(user_id=user_id)

    if status:
        query = query.filter_by(status=status)
    if type_filter:
        query = query.filter_by(type=type_filter)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return jsonify({
        'notifications': [notif.to_dict() for notif in notifications]
    }), 200


@notification_bp.route('/notifications/<int:notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(notification_id):
    notification = Notification.query.get(notification_id)

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    notification.status = 'read'
    notification.sent_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating notification', 'message': str(e)}), 500


@notification_bp.route('/send-reminder-batch', methods=['POST'])
def send_reminder_batch():
    """Enviar recordatorios para todas las citas del día siguiente"""
    # Esta ruta sería llamada por un cron job o scheduler
    tomorrow = datetime.utcnow().date() + timedelta(days=1)

    # Aquí deberías obtener las citas del día siguiente de la base de datos
    # Por simplicidad, retornamos un mensaje de éxito

    return jsonify({
        'message': f'Reminder batch process initiated for {tomorrow.isoformat()}',
        'status': 'processing'
    }), 200