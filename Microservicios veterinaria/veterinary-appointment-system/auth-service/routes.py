# auth-service/routes.py (modificado)
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
    # Nota: El registro público solo es para clientes
    # Los administradores registran al personal


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


# Instancias de schemas
register_schema = UserRegisterSchema()
login_schema = UserLoginSchema()


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = register_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verificar si el usuario ya existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 409

    # Crear nuevo usuario (siempre como cliente para el registro público)
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        role='client',
        specialization=None
    )
    user.set_password(data['password'])

    try:
        db.session.add(user)
        db.session.commit()

        # Crear token de acceso
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating user', 'message': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Buscar usuario
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403

    # Crear token de acceso
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'role': user.role  # Agregar el rol explícitamente para ayudar al frontend
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/veterinarians', methods=['GET'])
def get_veterinarians():
    veterinarians = User.query.filter_by(role='veterinarian', is_active=True).all()
    return jsonify({
        'veterinarians': [vet.to_dict() for vet in veterinarians]
    }), 200


@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    return jsonify({'valid': True}), 200


# Función para verificar permisos según rol
@auth_bp.route('/verify-role', methods=['GET'])
@jwt_required()
def verify_role():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    roles_allowed = request.args.getlist('roles')
    if not roles_allowed:
        return jsonify({'error': 'No roles specified'}), 400

    if user.role in roles_allowed:
        return jsonify({'valid': True, 'role': user.role}), 200
    else:
        return jsonify({'valid': False, 'message': 'Insufficient permissions', 'role': user.role}), 403