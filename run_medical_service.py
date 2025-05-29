#!/usr/bin/env python3
# run_medical_service.py
# Medical Service simplificado

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
    'REDIS_URL': 'redis://localhost:6379/3',
    'FLASK_ENV': 'development',
    'SECRET_KEY': 'dev-secret-key-medical',
    'UPLOAD_FOLDER': './uploads',
    'AUTH_SERVICE_URL': 'http://localhost:5001',
    'APPOINTMENT_SERVICE_URL': 'http://localhost:5002',
    'NOTIFICATION_SERVICE_URL': 'http://localhost:5003',
    'INVENTORY_SERVICE_URL': 'http://localhost:5005'
}

for key, value in env_vars.items():
    os.environ.setdefault(key, value)


def create_medical_app():
    """Crear la aplicación Medical Service"""
    from flask import Flask, Blueprint, request, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_cors import CORS
    from datetime import datetime, date
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
        'DEBUG': True,
        'UPLOAD_FOLDER': os.environ['UPLOAD_FOLDER']
    })

    # Crear directorio de uploads
    upload_folder = Path(app.config['UPLOAD_FOLDER'])
    upload_folder.mkdir(exist_ok=True)
    (upload_folder / 'pets').mkdir(exist_ok=True)
    (upload_folder / 'exams').mkdir(exist_ok=True)

    # Inicializar extensiones
    db = SQLAlchemy(app)
    CORS(app)

    # Modelo Pet
    class Pet(db.Model):
        __tablename__ = 'pets'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        owner_id = db.Column(db.String(36), nullable=False)
        name = db.Column(db.String(100), nullable=False)
        species = db.Column(db.String(50), nullable=False)
        breed = db.Column(db.String(100))
        birth_date = db.Column(db.Date)
        weight = db.Column(db.Numeric(5, 2))
        gender = db.Column(db.String(10))
        microchip_number = db.Column(db.String(50))
        photo_url = db.Column(db.Text)
        allergies = db.Column(db.Text)
        medical_notes = db.Column(db.Text)
        vaccination_status = db.Column(db.Text)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return {
                'id': self.id,
                'owner_id': self.owner_id,
                'name': self.name,
                'species': self.species,
                'breed': self.breed,
                'birth_date': self.birth_date.isoformat() if self.birth_date else None,
                'weight': float(self.weight) if self.weight else None,
                'gender': self.gender,
                'microchip_number': self.microchip_number,
                'photo_url': self.photo_url,
                'allergies': self.allergies,
                'medical_notes': self.medical_notes,
                'vaccination_status': self.vaccination_status,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

        def get_age(self):
            if self.birth_date:
                today = date.today()
                age = today.year - self.birth_date.year
                if today.month < self.birth_date.month or (
                        today.month == self.birth_date.month and today.day < self.birth_date.day):
                    age -= 1
                return age
            return None

    # Modelo MedicalRecord
    class MedicalRecord(db.Model):
        __tablename__ = 'medical_records'

        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        pet_id = db.Column(db.String(36), db.ForeignKey('pets.id'), nullable=False)
        veterinarian_id = db.Column(db.String(36), nullable=False)
        appointment_id = db.Column(db.String(36))

        symptoms_description = db.Column(db.Text)
        physical_examination = db.Column(db.Text)
        diagnosis = db.Column(db.Text)
        treatment = db.Column(db.Text)
        medications_prescribed = db.Column(db.Text)
        exams_requested = db.Column(db.Text)
        observations = db.Column(db.Text)
        next_appointment_recommendation = db.Column(db.Text)

        weight_at_visit = db.Column(db.Numeric(5, 2))
        temperature = db.Column(db.Numeric(4, 1))
        pulse = db.Column(db.Integer)
        respiratory_rate = db.Column(db.Integer)

        status = db.Column(db.Enum('draft', 'completed', 'reviewed', name='medical_record_status'), default='draft')
        is_emergency = db.Column(db.Boolean, default=False)

        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return {
                'id': self.id,
                'pet_id': self.pet_id,
                'veterinarian_id': self.veterinarian_id,
                'appointment_id': self.appointment_id,
                'symptoms_description': self.symptoms_description,
                'physical_examination': self.physical_examination,
                'diagnosis': self.diagnosis,
                'treatment': self.treatment,
                'medications_prescribed': self.medications_prescribed,
                'exams_requested': self.exams_requested,
                'observations': self.observations,
                'next_appointment_recommendation': self.next_appointment_recommendation,
                'weight_at_visit': float(self.weight_at_visit) if self.weight_at_visit else None,
                'temperature': float(self.temperature) if self.temperature else None,
                'pulse': self.pulse,
                'respiratory_rate': self.respiratory_rate,
                'status': self.status,
                'is_emergency': self.is_emergency,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

    # Servicios
    class MedicalService:
        @staticmethod
        def create_pet(pet_data):
            pet = Pet(
                owner_id=pet_data.get('owner_id'),
                name=pet_data.get('name'),
                species=pet_data.get('species'),
                breed=pet_data.get('breed'),
                birth_date=datetime.strptime(pet_data.get('birth_date'), '%Y-%m-%d').date() if pet_data.get(
                    'birth_date') else None,
                weight=pet_data.get('weight'),
                gender=pet_data.get('gender'),
                microchip_number=pet_data.get('microchip_number'),
                allergies=pet_data.get('allergies'),
                medical_notes=pet_data.get('medical_notes'),
                vaccination_status=pet_data.get('vaccination_status')
            )
            db.session.add(pet)
            db.session.commit()
            return pet

        @staticmethod
        def create_medical_record(record_data):
            medical_record = MedicalRecord(
                pet_id=record_data.get('pet_id'),
                veterinarian_id=record_data.get('veterinarian_id'),
                appointment_id=record_data.get('appointment_id'),
                symptoms_description=record_data.get('symptoms_description'),
                physical_examination=record_data.get('physical_examination'),
                diagnosis=record_data.get('diagnosis'),
                treatment=record_data.get('treatment'),
                medications_prescribed=record_data.get('medications_prescribed'),
                exams_requested=record_data.get('exams_requested'),
                observations=record_data.get('observations'),
                next_appointment_recommendation=record_data.get('next_appointment_recommendation'),
                weight_at_visit=record_data.get('weight_at_visit'),
                temperature=record_data.get('temperature'),
                pulse=record_data.get('pulse'),
                respiratory_rate=record_data.get('respiratory_rate'),
                is_emergency=record_data.get('is_emergency', False),
                status='draft'
            )
            db.session.add(medical_record)
            db.session.commit()
            return medical_record

    # Rutas
    medical_bp = Blueprint('medical', __name__)
    medical_service = MedicalService()

    @medical_bp.route('/pets', methods=['POST'])
    def create_pet():
        try:
            data = request.get_json()

            required_fields = ['owner_id', 'name', 'species']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            pet = medical_service.create_pet(data)

            return jsonify({
                'success': True,
                'message': 'Mascota creada exitosamente',
                'pet': pet.to_dict()
            }), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @medical_bp.route('/pets/<pet_id>', methods=['GET'])
    def get_pet(pet_id):
        try:
            pet = Pet.query.get(pet_id)
            if pet:
                pet_data = pet.to_dict()
                pet_data['age'] = pet.get_age()
                return jsonify({'success': True, 'pet': pet_data}), 200
            else:
                return jsonify({'success': False, 'message': 'Mascota no encontrada'}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @medical_bp.route('/pets/search', methods=['GET'])
    def search_pets():
        try:
            search_term = request.args.get('q', '')
            if not search_term:
                return jsonify({'success': False, 'message': 'Parámetro de búsqueda requerido'}), 400

            pets = Pet.query.filter(
                Pet.is_active == True,
                db.or_(
                    Pet.name.ilike(f'%{search_term}%'),
                    Pet.microchip_number.ilike(f'%{search_term}%'),
                    Pet.species.ilike(f'%{search_term}%'),
                    Pet.breed.ilike(f'%{search_term}%')
                )
            ).all()

            pets_data = []
            for pet in pets:
                pet_data = pet.to_dict()
                pet_data['age'] = pet.get_age()
                pets_data.append(pet_data)

            return jsonify({
                'success': True,
                'pets': pets_data,
                'total': len(pets_data),
                'search_term': search_term
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @medical_bp.route('/records', methods=['POST'])
    def create_medical_record():
        try:
            data = request.get_json()

            required_fields = ['pet_id', 'veterinarian_id']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'Campo requerido: {field}'}), 400

            medical_record = medical_service.create_medical_record(data)

            return jsonify({
                'success': True,
                'message': 'Historia clínica creada exitosamente',
                'medical_record': medical_record.to_dict()
            }), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @medical_bp.route('/summary/pet/<pet_id>', methods=['GET'])
    def get_medical_summary(pet_id):
        try:
            pet = Pet.query.get(pet_id)
            if not pet:
                return jsonify({'success': False, 'message': 'Mascota no encontrada'}), 404

            medical_records = MedicalRecord.query.filter_by(pet_id=pet_id).order_by(
                MedicalRecord.created_at.desc()).limit(5).all()

            summary = {
                'pet': pet.to_dict(),
                'total_visits': MedicalRecord.query.filter_by(pet_id=pet_id).count(),
                'last_visit': medical_records[0].created_at.isoformat() if medical_records else None,
                'recent_records': [record.to_dict() for record in medical_records],
                'allergies': pet.allergies,
                'vaccination_status': pet.vaccination_status
            }

            return jsonify({'success': True, 'summary': summary}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # Health check
    @app.route('/health')
    def health():
        try:
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'service': 'medical_service',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'medical_service',
                'database': 'disconnected',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    # Registrar blueprint
    app.register_blueprint(medical_bp, url_prefix='/medical')

    # Crear tablas
    with app.app_context():
        db.create_all()
        print("✅ Tablas de medical service creadas/verificadas")

    return app


def main():
    print("🚀 Iniciando Medical Service...")
    print(f"📂 Directorio: {ROOT_DIR}")
    print("🔧 Variables de entorno configuradas")

    try:
        app = create_medical_app()

        print("🎯 Configuración completada!")
        print("🌐 URLs disponibles:")
        print("   - Health Check: http://localhost:5004/health")
        print("   - Create Pet: http://localhost:5004/medical/pets")
        print("   - Search Pets: http://localhost:5004/medical/pets/search")
        print("   - Create Medical Record: http://localhost:5004/medical/records")
        print("   - Pet Summary: http://localhost:5004/medical/summary/pet/{pet_id}")
        print("")
        print("🚀 Medical Service iniciado en http://localhost:5004")
        print("💡 Presiona Ctrl+C para detener el servicio")
        print("=" * 60)

        app.run(host='0.0.0.0', port=5004, debug=True)

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()