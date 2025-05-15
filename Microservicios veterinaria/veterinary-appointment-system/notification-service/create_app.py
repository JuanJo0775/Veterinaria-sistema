# notification-service/create_app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # Configuración
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuración de email
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    # Inicializar extensiones
    db.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Ruta de salud
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'notification-service'}), 200

    # Importar y registrar rutas
    from routes import notification_bp
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')

    return app