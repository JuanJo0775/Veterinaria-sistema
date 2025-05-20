# auth-service/admin_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, post_load
from models import User
from db import db

admin_bp = Blueprint('admin', __name__)


class StaffSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=False)  # Opcional para actualizaciones
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    phone = fields.Str(required=False)
    role = fields.Str(required=True, validate=lambda x: x in ['veterinarian', 'receptionist', 'assistant', 'admin'])
    specialization = fields.Str(required=False)
    is_active = fields.Bool(load_default=True)

    @post_load
    def set_defaults(self, data, **kwargs):
        # Establecer valores predeterminados si no existen
        if 'is_active' not in data:
            data['is_active'] = True
        return data

# Instancias de schemas
staff_schema = StaffSchema()


# Middleware para verificar permisos de administrador
def admin_required(f):
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403

        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Rutas para administración de personal
@admin_bp.route('/staff', methods=['POST'])
@admin_required
def create_staff():
    try:
        data = staff_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verificar si el usuario ya existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 409

    # Crear nuevo miembro del personal
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        role=data['role'],
        specialization=data.get('specialization') if data['role'] == 'veterinarian' else None,
        is_active=data.get('is_active', True)
    )

    # Si se proporcionó contraseña, establecerla, de lo contrario usar una predeterminada
    password = data.get('password', 'changeme123')
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'Staff member created successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating staff member', 'message': str(e)}), 500


@admin_bp.route('/staff', methods=['GET'])
@admin_required
def get_all_staff():
    role = request.args.get('role')
    is_active = request.args.get('is_active')

    query = User.query.filter(User.role != 'client')

    if role:
        query = query.filter_by(role=role)

    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)

    staff = query.all()

    return jsonify({
        'staff': [user.to_dict() for user in staff]
    }), 200


@admin_bp.route('/staff/<int:user_id>', methods=['GET'])
@admin_required
def get_staff_member(user_id):
    user = User.query.get(user_id)

    if not user or user.role == 'client':
        return jsonify({'error': 'Staff member not found'}), 404

    return jsonify({'user': user.to_dict()}), 200


@admin_bp.route('/staff/<int:user_id>', methods=['PUT'])
@admin_required
def update_staff_member(user_id):
    user = User.query.get(user_id)

    if not user or user.role == 'client':
        return jsonify({'error': 'Staff member not found'}), 404

    data = request.json

    # Actualizar campos permitidos
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already in use'}), 409
        user.email = data['email']

    if 'password' in data and data['password']:
        user.set_password(data['password'])

    if 'first_name' in data:
        user.first_name = data['first_name']

    if 'last_name' in data:
        user.last_name = data['last_name']

    if 'phone' in data:
        user.phone = data['phone']

    if 'role' in data:
        if data['role'] not in ['admin', 'veterinarian', 'receptionist', 'assistant']:
            return jsonify({'error': 'Invalid role'}), 400
        user.role = data['role']

    if 'specialization' in data and user.role == 'veterinarian':
        user.specialization = data['specialization']

    if 'is_active' in data:
        user.is_active = data['is_active']

    try:
        db.session.commit()
        return jsonify({
            'message': 'Staff member updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating staff member', 'message': str(e)}), 500


@admin_bp.route('/staff/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_staff_member(user_id):
    user = User.query.get(user_id)

    if not user or user.role == 'client':
        return jsonify({'error': 'Staff member not found'}), 404

    # No eliminar realmente, solo desactivar
    user.is_active = False

    try:
        db.session.commit()
        return jsonify({'message': 'Staff member deactivated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error deactivating staff member', 'message': str(e)}), 500


# Rutas para administración de clientes
@admin_bp.route('/clients', methods=['GET'])
@admin_required
def get_all_clients():
    is_active = request.args.get('is_active')

    query = User.query.filter_by(role='client')

    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)

    clients = query.all()

    return jsonify({
        'clients': [user.to_dict() for user in clients]
    }), 200


@admin_bp.route('/clients/<int:user_id>', methods=['GET'])
@admin_required
def get_client(user_id):
    user = User.query.filter_by(id=user_id, role='client').first()

    if not user:
        return jsonify({'error': 'Client not found'}), 404

    return jsonify({'client': user.to_dict()}), 200


@admin_bp.route('/clients/<int:user_id>', methods=['PUT'])
@admin_required
def update_client(user_id):
    user = User.query.filter_by(id=user_id, role='client').first()

    if not user:
        return jsonify({'error': 'Client not found'}), 404

    data = request.json

    # Actualizar campos permitidos
    if 'is_active' in data:
        user.is_active = data['is_active']

    try:
        db.session.commit()
        return jsonify({
            'message': 'Client updated successfully',
            'client': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error updating client', 'message': str(e)}), 500


# Rutas para estadísticas del panel de administración
@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    # Contar usuarios por rol
    total_vets = User.query.filter_by(role='veterinarian', is_active=True).count()
    total_receptionists = User.query.filter_by(role='receptionist', is_active=True).count()
    total_assistants = User.query.filter_by(role='assistant', is_active=True).count()
    total_clients = User.query.filter_by(role='client', is_active=True).count()

    return jsonify({
        'staff_stats': {
            'veterinarians': total_vets,
            'receptionists': total_receptionists,
            'assistants': total_assistants,
            'clients': total_clients,
            'total_staff': total_vets + total_receptionists + total_assistants
        }
    }), 200

# Más rutas para configuraciones, etc.