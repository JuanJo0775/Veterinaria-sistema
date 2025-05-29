#!/usr/bin/env python3
# simple_auth_runner.py
# Versión simplificada que evita imports relativos

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
    'REDIS_URL': 'redis://localhost:6379/0',
    'FLASK_ENV': 'development',
    'SECRET_KEY': 'dev-secret-key-auth',
    'JWT_SECRET_KEY': 'dev-jwt-secret-key'
}

for key, value in env_vars.items():
    os.environ.setdefault(key, value)


def create_simple_auth_app():
    """Crear la aplicación Flask sin imports relativos complejos"""
    from flask import Flask, Blueprint, request, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_cors import CORS
    from werkzeug.security import generate_password_hash, check_password_hash
    import jwt
    from datetime import datetime, timedelta
    import uuid

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

    # Modelo User simplificado
    class User(db.Model):
        __tablename__ = 'users'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)
        role = db.Column(db.Enum('client', 'veterinarian', 'receptionist', 'auxiliary', 'admin', name='user_role_enum'),
                         nullable=False, default='client')
        first_name = db.Column(db.String(50), nullable=False)
        last_name = db.Column(db.String(50), nullable=False)
        phone = db.Column(db.String(15))
        address = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        is_active = db.Column(db.Boolean, default=True)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

        def to_dict(self):
            return {
                'id': self.id,
                'email': self.email,
                'role': self.role,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'phone': self.phone,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    # Servicios simplificados
    class AuthService:
        @staticmethod
        def generate_token(user):
            payload = {
                'user_id': user.id,
                'email': user.email,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

        @staticmethod
        def verify_token(token):
            try:
                payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                return User.query.get(payload['user_id'])
            except:
                return None

        @staticmethod
        def create_user(user_data):
            user = User(
                email=user_data.get('email'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                phone=user_data.get('phone'),
                address=user_data.get('address'),
                role=user_data.get('role', 'client')
            )
            user.set_password(user_data.get('password'))
            db.session.add(user)
            db.session.commit()
            return user

    # Rutas
    auth_bp = Blueprint('auth', __name__)
    auth_service = AuthService()

    @auth_bp.route('/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password) and user.is_active:
                token = auth_service.generate_token(user)
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'role': user.role,
                        'name': f"{user.first_name} {user.last_name}"
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Credenciales inválidas'
                }), 401
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @auth_bp.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()

            # Verificar email único
            if User.query.filter_by(email=data.get('email')).first():
                return jsonify({
                    'success': False,
                    'message': 'Email ya registrado'
                }), 400

            user = auth_service.create_user(data)
            return jsonify({
                'success': True,
                'message': 'Usuario creado exitosamente',
                'user_id': user.id
            }), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @auth_bp.route('/verify', methods=['POST'])
    def verify_token():
        try:
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            user = auth_service.verify_token(token)

            if user:
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'role': user.role,
                        'name': f"{user.first_name} {user.last_name}"
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Token inválido'
                }), 401
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # Health check
    @app.route('/health')
    def health():
        try:
            # Test DB connection
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'service': 'auth_service',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'auth_service',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    # Registrar blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Crear tablas
    with app.app_context():
        db.create_all()
        print("✅ Tablas de base de datos creadas/verificadas")

    return app


def main():
    print("🚀 Iniciando Auth Service (versión simplificada)...")
    print(f"📂 Directorio: {ROOT_DIR}")
    print("🔧 Variables de entorno configuradas")

    try:
        app = create_simple_auth_app()

        print("🎯 Configuración completada!")
        print("🌐 URLs disponibles:")
        print("   - Health Check: http://localhost:5001/health")
        print("   - Login: http://localhost:5001/auth/login")
        print("   - Register: http://localhost:5001/auth/register")
        print("   - Verify Token: http://localhost:5001/auth/verify")
        print("")
        print("🚀 Auth Service iniciado en http://localhost:5001")
        print("💡 Presiona Ctrl+C para detener el servicio")
        print("=" * 60)

        app.run(host='0.0.0.0', port=5001, debug=True)

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()