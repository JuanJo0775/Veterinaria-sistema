# auth-service/routes.py (CORREGIDO)
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from models import User
from db import db

auth_bp = Blueprint('auth', __name__)


# Schemas de validación
class UserRegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 6)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    phone = fields.Str(required=False)


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


# Instancias de schemas
register_schema = UserRegisterSchema()
login_schema = UserLoginSchema()


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # Obtener y validar datos JSON
        if not request.json:
            return jsonify({'error': 'No se proporcionaron datos JSON'}), 400

        data = register_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        return jsonify({'error': f'Error en los datos: {str(e)}'}), 400

    try:
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Ya existe un usuario con este email'}), 409

        # Crear nuevo usuario (siempre como cliente para el registro público)
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            role='client',
            is_active=True
        )

        # Establecer contraseña
        user.set_password(data['password'])

        # Guardar en base de datos
        db.session.add(user)
        db.session.commit()

        # Crear token de acceso
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al crear usuario', 'message': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        if not request.json:
            return jsonify({'error': 'No se proporcionaron datos JSON'}), 400

        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    try:
        # Buscar usuario
        user = User.query.filter_by(email=data['email']).first()

        if not user:
            return jsonify({'error': 'Email o contraseña incorrectos'}), 401

        if not user.check_password(data['password']):
            return jsonify({'error': 'Email o contraseña incorrectos'}), 401

        if not user.is_active:
            return jsonify({'error': 'La cuenta está inactiva. Contacte al administrador'}), 403

        # Crear token de acceso
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user': user.to_dict(),
            'access_token': access_token,
            'role': user.role
        }), 200

    except Exception as e:
        return jsonify({'error': 'Error en el servidor', 'message': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener usuario', 'message': str(e)}), 500


@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener usuario', 'message': str(e)}), 500


@auth_bp.route('/veterinarians', methods=['GET'])
def get_veterinarians():
    try:
        veterinarians = User.query.filter_by(role='veterinarian', is_active=True).all()
        return jsonify({
            'veterinarians': [vet.to_dict() for vet in veterinarians]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener veterinarios', 'message': str(e)}), 500


@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_active:
            return jsonify({'valid': False, 'message': 'Token inválido o usuario inactivo'}), 401

        return jsonify({'valid': True, 'user_id': user_id}), 200
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)}), 401


@auth_bp.route('/verify-role', methods=['GET'])
@jwt_required()
def verify_role():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        roles_allowed = request.args.getlist('roles')
        if not roles_allowed:
            return jsonify({'error': 'No se especificaron roles'}), 400

        if user.role in roles_allowed:
            return jsonify({'valid': True, 'role': user.role}), 200
        else:
            return jsonify({'valid': False, 'message': 'Permisos insuficientes', 'role': user.role}), 403

    except Exception as e:
        return jsonify({'error': 'Error al verificar rol', 'message': str(e)}), 500