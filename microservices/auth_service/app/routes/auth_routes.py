# microservices/auth_service/app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash

from datetime import datetime, timedelta
from ..models.user import User, db
from ..services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = auth_service.authenticate_user(email, password)

        if user:
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
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validar que el email no exista
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
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/change-password', methods=['PUT'])
def change_password():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = auth_service.verify_token(token)

        if not user:
            return jsonify({
                'success': False,
                'message': 'Token inválido'
            }), 401

        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if auth_service.change_password(user.id, old_password, new_password):
            return jsonify({
                'success': True,
                'message': 'Contraseña actualizada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Contraseña actual incorrecta'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = auth_service.verify_token(token)

        if user:
            return jsonify({
                'success': True,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Token inválido'
            }), 401

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = auth_service.verify_token(token)

        if not user:
            return jsonify({
                'success': False,
                'message': 'Token inválido'
            }), 401

        data = request.get_json()
        updated_user = auth_service.update_user(user.id, data)

        if updated_user:
            return jsonify({
                'success': True,
                'message': 'Perfil actualizado exitosamente',
                'user': updated_user.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Error al actualizar perfil'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'auth_service'
    }), 200