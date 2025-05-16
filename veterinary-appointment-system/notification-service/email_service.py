# notification-service/email_service.py
from flask_mail import Message
from create_app import mail, db  # Importar desde create_app
from datetime import datetime


class EmailService:
    @staticmethod
    def send_appointment_confirmation(user_email, appointment_details):
        subject = "Confirmación de Cita Veterinaria"
        body = f"""
        <h2>Confirmación de Cita</h2>
        <p>Estimado(a) {appointment_details.get('client_name')},</p>
        <p>Su cita ha sido confirmada con los siguientes detalles:</p>
        <ul>
            <li><strong>Fecha:</strong> {appointment_details.get('date')}</li>
            <li><strong>Hora:</strong> {appointment_details.get('time')}</li>
            <li><strong>Veterinario:</strong> {appointment_details.get('veterinarian_name')}</li>
            <li><strong>Mascota:</strong> {appointment_details.get('pet_name')}</li>
            <li><strong>Motivo:</strong> {appointment_details.get('reason')}</li>
        </ul>
        <p>Por favor, llegue 10 minutos antes de su cita.</p>
        <p>Saludos cordiales,<br>Clínica Veterinaria</p>
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=body
        )

        try:
            mail.send(msg)
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_appointment_reminder(user_email, appointment_details):
        subject = "Recordatorio de Cita Veterinaria"
        body = f"""
        <h2>Recordatorio de Cita</h2>
        <p>Estimado(a) {appointment_details.get('client_name')},</p>
        <p>Le recordamos que tiene una cita mañana:</p>
        <ul>
            <li><strong>Fecha:</strong> {appointment_details.get('date')}</li>
            <li><strong>Hora:</strong> {appointment_details.get('time')}</li>
            <li><strong>Veterinario:</strong> {appointment_details.get('veterinarian_name')}</li>
            <li><strong>Mascota:</strong> {appointment_details.get('pet_name')}</li>
        </ul>
        <p>Si necesita cancelar o reprogramar, por favor contáctenos.</p>
        <p>Saludos cordiales,<br>Clínica Veterinaria</p>
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=body
        )

        try:
            mail.send(msg)
            return True, "Reminder sent successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_appointment_cancellation(user_email, appointment_details):
        subject = "Cancelación de Cita Veterinaria"
        body = f"""
        <h2>Cancelación de Cita</h2>
        <p>Estimado(a) {appointment_details.get('client_name')},</p>
        <p>Su cita ha sido cancelada:</p>
        <ul>
            <li><strong>Fecha:</strong> {appointment_details.get('date')}</li>
            <li><strong>Hora:</strong> {appointment_details.get('time')}</li>
            <li><strong>Veterinario:</strong> {appointment_details.get('veterinarian_name')}</li>
        </ul>
        <p>Si desea reprogramar, puede hacerlo a través de nuestra plataforma.</p>
        <p>Saludos cordiales,<br>Clínica Veterinaria</p>
        """

        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=body
        )

        try:
            mail.send(msg)
            return True, "Cancellation email sent successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_vet_new_appointment(vet_email, appointment_details):
        subject = "Nueva Cita Agendada"
        body = f"""
        <h2>Nueva Cita</h2>
        <p>Dr(a). {appointment_details.get('veterinarian_name')},</p>
        <p>Se ha agendado una nueva cita:</p>
        <ul>
            <li><strong>Fecha:</strong> {appointment_details.get('date')}</li>
            <li><strong>Hora:</strong> {appointment_details.get('time')}</li>
            <li><strong>Cliente:</strong> {appointment_details.get('client_name')}</li>
            <li><strong>Mascota:</strong> {appointment_details.get('pet_name')}</li>
            <li><strong>Motivo:</strong> {appointment_details.get('reason')}</li>
        </ul>
        <p>Puede revisar más detalles en el sistema.</p>
        <p>Saludos cordiales,<br>Sistema de Citas Veterinarias</p>
        """

        msg = Message(
            subject=subject,
            recipients=[vet_email],
            html=body
        )

        try:
            mail.send(msg)
            return True, "Email sent to veterinarian"
        except Exception as e:
            return False, str(e)