#!/usr/bin/env python3
# run_inventory_service.py
# Inventory Service simplificado

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
    'REDIS_URL': 'redis://localhost:6379/4',
    'FLASK_ENV': 'development',
    'SECRET_KEY': 'dev-secret-key-inventory',
    'AUTO_ALERTS_ENABLED': 'true',
    'LOW_STOCK_THRESHOLD_DAYS': '7',
    'AUTH_SERVICE_URL': 'http://localhost:5001',
    'APPOINTMENT_SERVICE_URL': 'http://localhost:5002',
    'NOTIFICATION_SERVICE_URL': 'http://localhost:5003',
    'MEDICAL_SERVICE_URL': 'http://localhost:5004'
}

for key, value in env_vars.items():
    os.environ.setdefault(key, value)


def create_inventory_app():
    """Crear la aplicación Inventory Service"""
    from flask import Flask, Blueprint, request, jsonify, make_response
    from flask_sqlalchemy import SQLAlchemy
    from flask_cors import CORS
    from datetime import datetime, date, timedelta
    import uuid
    import csv
    import io

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

    # Modelo Medication
    class Medication(db.Model):
        __tablename__ = 'medications'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        name = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text)
        stock_quantity = db.Column(db.Integer, nullable=False, default=0)
        unit_price = db.Column(db.Numeric(10, 2), nullable=False)
        expiration_date = db.Column(db.Date)
        supplier = db.Column(db.String(255))
        minimum_stock_alert = db.Column(db.Integer, default=10)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Campos adicionales
        category = db.Column(db.String(100))
        presentation = db.Column(db.String(100))
        concentration = db.Column(db.String(50))
        laboratory = db.Column(db.String(255))
        batch_number = db.Column(db.String(50))
        storage_conditions = db.Column(db.Text)
        is_active = db.Column(db.Boolean, default=True)

        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'stock_quantity': self.stock_quantity,
                'unit_price': float(self.unit_price) if self.unit_price else None,
                'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
                'supplier': self.supplier,
                'minimum_stock_alert': self.minimum_stock_alert,
                'category': self.category,
                'presentation': self.presentation,
                'concentration': self.concentration,
                'laboratory': self.laboratory,
                'batch_number': self.batch_number,
                'storage_conditions': self.storage_conditions,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'days_to_expiration': self.get_days_to_expiration(),
                'stock_status': self.get_stock_status()
            }

        def get_days_to_expiration(self):
            if self.expiration_date:
                delta = self.expiration_date - date.today()
                return delta.days
            return None

        def get_stock_status(self):
            if self.stock_quantity <= 0:
                return 'out_of_stock'
            elif self.stock_quantity <= self.minimum_stock_alert:
                return 'low_stock'
            else:
                return 'in_stock'

    # Modelo StockMovement
    class StockMovement(db.Model):
        __tablename__ = 'stock_movements'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        medication_id = db.Column(db.String(36), db.ForeignKey('medications.id'), nullable=False)
        movement_type = db.Column(db.Enum('in', 'out', 'adjustment', name='movement_type_enum'), nullable=False)
        quantity = db.Column(db.Integer, nullable=False)
        previous_stock = db.Column(db.Integer, nullable=False)
        new_stock = db.Column(db.Integer, nullable=False)
        reason = db.Column(db.String(255))
        reference_id = db.Column(db.String(36))
        user_id = db.Column(db.String(36))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        unit_cost = db.Column(db.Numeric(10, 2))
        notes = db.Column(db.Text)

        def to_dict(self):
            return {
                'id': self.id,
                'medication_id': self.medication_id,
                'movement_type': self.movement_type,
                'quantity': self.quantity,
                'previous_stock': self.previous_stock,
                'new_stock': self.new_stock,
                'reason': self.reason,
                'reference_id': self.reference_id,
                'user_id': self.user_id,
                'unit_cost': float(self.unit_cost) if self.unit_cost else None,
                'notes': self.notes,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    # Servicios
    class InventoryService:
        @staticmethod
        def create_medication(medication_data):
            medication = Medication(
                name=medication_data.get('name'),
                description=medication_data.get('description'),
                stock_quantity=medication_data.get('stock_quantity', 0),
                unit_price=medication_data.get('unit_price'),
                expiration_date=datetime.strptime(medication_data.get('expiration_date'),
                                                  '%Y-%m-%d').date() if medication_data.get(
                    'expiration_date') else None,
                supplier=medication_data.get('supplier'),
                minimum_stock_alert=medication_data.get('minimum_stock_alert', 10),
                category=medication_data.get('category'),
                presentation=medication_data.get('presentation'),
                concentration=medication_data.get('concentration'),
                laboratory=medication_data.get('laboratory'),
                batch_number=medication_data.get('batch_number'),
                storage_conditions=medication_data.get('storage_conditions')
            )
            db.session.add(medication)
            db.session.commit()

            # Registrar movimiento inicial si hay stock
            if medication.stock_quantity > 0:
                InventoryService._record_stock_movement(
                    medication.id, 'in', medication.stock_quantity, 0, medication.stock_quantity, 'Inventario inicial'
                )

            return medication

        @staticmethod
        def update_stock(medication_id, quantity_change, reason, reference_id=None, user_id=None):
            medication = Medication.query.get(medication_id)
            if not medication:
                return None

            previous_stock = medication.stock_quantity
            new_stock = previous_stock + quantity_change

            if new_stock < 0:
                raise ValueError("Stock insuficiente")

            medication.stock_quantity = new_stock
            movement_type = 'in' if quantity_change > 0 else 'out'

            movement = InventoryService._record_stock_movement(
                medication_id, movement_type, abs(quantity_change), previous_stock, new_stock, reason, reference_id,
                user_id
            )

            db.session.commit()

            return {
                'medication': medication,
                'movement': movement,
                'previous_stock': previous_stock,
                'new_stock': new_stock
            }

        @staticmethod
        def _record_stock_movement(medication_id, movement_type, quantity, previous_stock, new_stock, reason,
                                   reference_id=None, user_id=None):
            movement = StockMovement(
                medication_id=medication_id,
                movement_type=movement_type,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                reason=reason,
                reference_id=reference_id,
                user_id=user_id
            )
            db.session.add(movement)
            return movement

        @staticmethod
        def get_low_stock_medications():
            return Medication.query.filter(
                Medication.is_active == True,
                Medication.stock_quantity <= Medication.minimum_stock_alert
            ).all()

        @staticmethod
        def get_expiring_medications(days_threshold=30):
            expiration_limit = date.today() + timedelta(days=days_threshold)
            return Medication.query.filter(
                Medication.is_active == True,
                Medication.expiration_date <= expiration_limit,
                Medication.expiration_date >= date.today()
            ).all()

        @staticmethod
        def search_medications(search_term):
            return Medication.query.filter(
                Medication.is_active == True,
                db.or_(
                    Medication.name.ilike(f'%{search_term}%'),
                    Medication.category.ilike(f'%{search_term}%'),
                    Medication.laboratory.ilike(f'%{search_term}%'),
                    Medication.supplier.ilike(f'%{search_term}%')
                )
            ).all()

    # Rutas
    inventory_bp = Blueprint('inventory', __name__)
    inventory_service = InventoryService()

    @inventory_bp.route('/medications', methods=['POST'])
    def create_medication():
        try:
            data = request.get_json()

            required_fields = ['name', 'unit_price']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            medication = inventory_service.create_medication(data)

            return jsonify({
                'success': True,
                'message': 'Medicamento creado exitosamente',
                'medication': medication.to_dict()
            }), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/medications', methods=['GET'])
    def get_medications():
        try:
            include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
            category = request.args.get('category')

            query = Medication.query
            if not include_inactive:
                query = query.filter_by(is_active=True)
            if category:
                query = query.filter_by(category=category)

            medications = query.order_by(Medication.name).all()
            medications_data = [med.to_dict() for med in medications]

            return jsonify({
                'success': True,
                'medications': medications_data,
                'total': len(medications_data)
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/medications/<medication_id>', methods=['GET'])
    def get_medication(medication_id):
        try:
            medication = Medication.query.get(medication_id)
            if medication:
                medication_data = medication.to_dict()
                # Incluir movimientos recientes
                recent_movements = StockMovement.query.filter_by(medication_id=medication_id).order_by(
                    StockMovement.created_at.desc()).limit(10).all()
                medication_data['recent_movements'] = [movement.to_dict() for movement in recent_movements]

                return jsonify({'success': True, 'medication': medication_data}), 200
            else:
                return jsonify({'success': False, 'message': 'Medicamento no encontrado'}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/medications/search', methods=['GET'])
    def search_medications():
        try:
            search_term = request.args.get('q', '')
            if not search_term:
                return jsonify({'success': False, 'message': 'Parámetro de búsqueda requerido'}), 400

            medications = inventory_service.search_medications(search_term)
            medications_data = [med.to_dict() for med in medications]

            return jsonify({
                'success': True,
                'medications': medications_data,
                'total': len(medications_data),
                'search_term': search_term
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/add-stock', methods=['POST'])
    def add_stock():
        try:
            data = request.get_json()

            required_fields = ['medication_id', 'quantity', 'reason']
            for field in required_fields:
                if field not in data:
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            result = inventory_service.update_stock(
                data.get('medication_id'),
                data.get('quantity'),
                data.get('reason'),
                data.get('reference_id'),
                data.get('user_id')
            )

            return jsonify({
                'success': True,
                'message': 'Stock agregado exitosamente',
                'result': {
                    'medication': result['medication'].to_dict(),
                    'previous_stock': result['previous_stock'],
                    'new_stock': result['new_stock'],
                    'movement': result['movement'].to_dict()
                }
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/reduce-stock', methods=['POST'])
    def reduce_stock():
        try:
            data = request.get_json()

            required_fields = ['medication_id', 'quantity', 'reason']
            for field in required_fields:
                if field not in data:
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            result = inventory_service.update_stock(
                data.get('medication_id'),
                -data.get('quantity'),  # Cantidad negativa para reducir
                data.get('reason'),
                data.get('reference_id'),
                data.get('user_id')
            )

            return jsonify({
                'success': True,
                'message': 'Stock reducido exitosamente',
                'result': {
                    'medication': result['medication'].to_dict(),
                    'previous_stock': result['previous_stock'],
                    'new_stock': result['new_stock'],
                    'movement': result['movement'].to_dict()
                }
            }), 200
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/movements', methods=['GET'])
    def get_stock_movements():
        try:
            medication_id = request.args.get('medication_id')
            limit = request.args.get('limit')

            query = StockMovement.query
            if medication_id:
                query = query.filter_by(medication_id=medication_id)

            query = query.order_by(StockMovement.created_at.desc())

            if limit:
                query = query.limit(int(limit))

            movements = query.all()
            movements_data = [movement.to_dict() for movement in movements]

            return jsonify({
                'success': True,
                'movements': movements_data,
                'total': len(movements_data)
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/alerts/low-stock', methods=['GET'])
    def get_low_stock_alerts():
        try:
            medications = inventory_service.get_low_stock_medications()
            medications_data = [med.to_dict() for med in medications]

            return jsonify({
                'success': True,
                'low_stock_medications': medications_data,
                'total': len(medications_data)
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/alerts/expiring', methods=['GET'])
    def get_expiring_medications():
        try:
            days_threshold = int(request.args.get('days', 30))
            medications = inventory_service.get_expiring_medications(days_threshold)
            medications_data = [med.to_dict() for med in medications]

            return jsonify({
                'success': True,
                'expiring_medications': medications_data,
                'total': len(medications_data),
                'days_threshold': days_threshold
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/summary', methods=['GET'])
    def get_inventory_summary():
        try:
            medications = Medication.query.filter_by(is_active=True).all()

            total_medications = len(medications)
            total_value = sum(float(med.unit_price or 0) * med.stock_quantity for med in medications)
            low_stock_count = len([med for med in medications if med.get_stock_status() == 'low_stock'])
            out_of_stock_count = len([med for med in medications if med.get_stock_status() == 'out_of_stock'])
            expiring_count = len([med for med in medications if
                                  med.get_days_to_expiration() and 0 <= med.get_days_to_expiration() <= 30])

            summary = {
                'total_medications': total_medications,
                'total_inventory_value': total_value,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'expiring_soon_count': expiring_count,
                'last_updated': datetime.now().isoformat()
            }

            return jsonify({'success': True, 'summary': summary}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/categories', methods=['GET'])
    def get_categories():
        try:
            categories = db.session.query(Medication.category).filter(
                Medication.category.isnot(None),
                Medication.is_active == True
            ).distinct().all()

            categories_list = [cat[0] for cat in categories if cat[0]]

            return jsonify({
                'success': True,
                'categories': sorted(categories_list)
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @inventory_bp.route('/stats', methods=['GET'])
    def get_inventory_stats():
        try:
            total_medications = Medication.query.filter_by(is_active=True).count()
            low_stock = len(inventory_service.get_low_stock_medications())
            expiring_soon = len(inventory_service.get_expiring_medications(30))

            # Estadísticas por categoría
            category_stats = db.session.query(
                Medication.category,
                db.func.count(Medication.id).label('count'),
                db.func.sum(Medication.stock_quantity).label('total_stock')
            ).filter(
                Medication.is_active == True,
                Medication.category.isnot(None)
            ).group_by(Medication.category).all()

            return jsonify({
                'success': True,
                'stats': {
                    'total_medications': total_medications,
                    'low_stock_count': low_stock,
                    'expiring_soon_count': expiring_soon,
                    'category_stats': [
                        {
                            'category': stat[0],
                            'medication_count': stat[1],
                            'total_stock': stat[2] or 0
                        }
                        for stat in category_stats
                    ]
                }
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
                'service': 'inventory_service',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'inventory_service',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    # Registrar blueprint
    app.register_blueprint(inventory_bp, url_prefix='/inventory')

    # Crear tablas
    with app.app_context():
        db.create_all()
        print("✅ Tablas de inventory service creadas/verificadas")

    return app


def main():
    print("🚀 Iniciando Inventory Service...")
    print(f"📂 Directorio: {ROOT_DIR}")
    print("🔧 Variables de entorno configuradas")

    try:
        app = create_inventory_app()

        print("🎯 Configuración completada!")
        print("🌐 URLs disponibles:")
        print("   - Health Check: http://localhost:5005/health")
        print("   - Create Medication: http://localhost:5005/inventory/medications")
        print("   - Search Medications: http://localhost:5005/inventory/medications/search")
        print("   - Add Stock: http://localhost:5005/inventory/add-stock")
        print("   - Reduce Stock: http://localhost:5005/inventory/reduce-stock")
        print("   - Low Stock Alerts: http://localhost:5005/inventory/alerts/low-stock")
        print("   - Expiring Medications: http://localhost:5005/inventory/alerts/expiring")
        print("   - Inventory Summary: http://localhost:5005/inventory/summary")
        print("")
        print("🚀 Inventory Service iniciado en http://localhost:5005")
        print("💡 Presiona Ctrl+C para detener el servicio")
        print("=" * 60)

        app.run(host='0.0.0.0', port=5005, debug=True)

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()