# 🐾 Sistema de Gestión Veterinaria - Aplicación de Consola

## 📋 Descripción

Esta aplicación de consola sirve como **frontend de testing y desarrollo** para el sistema de gestión veterinaria basado en microservicios. Permite:

- ✅ **Gestión automática de servicios** (inicio, parada, verificación)
- 🧪 **Testing completo de APIs** de todos los microservicios
- 📊 **Generación de reportes** detallados
- 🔍 **Inspección de datos** en tiempo real
- 🛠 **Herramientas de desarrollo** avanzadas
- 📈 **Benchmark y monitoreo** de rendimiento

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                   APLICACIÓN DE CONSOLA                     │
├─────────────────────────────────────────────────────────────┤
│  • Gestión de Servicios Docker                              │
│  • Testing Automatizado de APIs                             │
│  • Generación de Datos de Prueba                            │
│  • Reportes y Monitoreo                                     │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    MICROSERVICIOS                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Auth Service   │ Medical Service │   Notification Service  │
│   (Port 5001)   │   (Port 5004)   │      (Port 5003)        │
├─────────────────┼─────────────────┼─────────────────────────┤
│Appointment Svc  │ Inventory Svc   │     Gateway (5000)      │
│   (Port 5002)   │   (Port 5005)   │                         │
└─────────────────┴─────────────────┴─────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  INFRAESTRUCTURA                            │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL (5432)  │  Redis (6379)  │  Docker Compose      │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de la palicacion consola

```
console_app/
├── main.py              # Aplicación principal
├── utils.py             # Utilidades y clases helper
├── config.py            # Configuración
├── requirements.txt     # Dependencias Python
├── run_console.sh       # Script de inicio
├── reports/             # Directorio de reportes (auto-creado)
└── README.md           # Este archivo
```

## 🔧 Instalación y Configuración

### Prerequisitos

1. **Python 3.8+**
2. **Docker & Docker Compose**
3. **Make** (opcional, para comandos simplificados)
4. **Git** (para clonar el repositorio)

### Paso 1: Preparar el Entorno

```bash
# Navegar al directorio del proyecto principal
cd veterinary_clinic_system

# Crear directorio para la aplicación de consola
mkdir -p console_app
cd console_app

# Copiar los archivos de la aplicación de consola
# (main.py, utils.py, config.py, requirements.txt, run_console.sh)
```

### Paso 2: Configurar Permisos

```bash
# Hacer ejecutable el script de inicio
chmod +x run_console.sh

# Verificar permisos del proyecto padre
chmod +x ../scripts/*.sh
```

### Paso 3: Instalación Automática

```bash
# Opción 1: Usar el script automático (Recomendado)
./run_console.sh

# Opción 2: Instalación manual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

## 🚀 Uso de la Aplicación

### Inicio Rápido

```bash
# Ejecutar la aplicación
./run_console.sh

# O manualmente
cd console_app
python3 main.py
```

### Menú Principal

Al ejecutar la aplicación, verás el menú principal:

```
🐾 SISTEMA DE GESTIÓN VETERINARIA - CONSOLA
════════════════════════════════════════════════════════════

Estado de servicios:
  🟢 auth Service
  🟢 appointment Service  
  🟢 notification Service
  🟢 medical Service
  🟢 inventory Service

Usuario actual: test@example.com (client)

OPCIONES DISPONIBLES:
1. 🚀 Iniciar servicios
2. 🔍 Verificar servicios
3. 🧪 Ejecutar tests completos
4. 👤 Tests de autenticación
5. 🏥 Tests de servicio médico
6. 💊 Tests de inventario
7. 📅 Tests de citas
8. 📧 Tests de notificaciones
9. 📊 Crear datos de ejemplo
10. 📈 Ver resumen del sistema
11. 🛑 Detener servicios
0. ❌ Salir
```

## 📖 Guía de Funcionalidades

### 1. 🚀 Gestión de Servicios

#### Iniciar Servicios
```bash
# La aplicación ejecuta automáticamente:
make dev-up
# O como fallback:
docker-compose -f ../docker-compose.dev.yml up -d
```

#### Verificar Estado
- ✅ Verifica conectividad de cada servicio
- 📊 Muestra métricas de salud (CPU, memoria, uptime)
- ⚡ Mide tiempos de respuesta

#### Detener Servicios
```bash
# Detiene todos los servicios
make dev-down
```

### 2. 🧪 Testing Automatizado

#### Tests Completos
Ejecuta una suite completa que incluye:

1. **Conectividad** - Health checks de todos los servicios
2. **Autenticación** - Registro, login, verificación de tokens
3. **Servicios Médicos** - CRUD de mascotas e historias clínicas
4. **Inventario** - Gestión de medicamentos y stock
5. **Citas** - Creación y gestión de citas
6. **Notificaciones** - Envío de emails y WhatsApp

#### Tests Individuales
- **Auth Service**: Registro, login, tokens, perfiles
- **Medical Service**: Mascotas, historias clínicas, prescripciones
- **Inventory Service**: Medicamentos, stock, alertas
- **Appointment Service**: Citas, disponibilidad, confirmaciones
- **Notification Service**: Emails, WhatsApp, recordatorios

### 3. 📊 Datos de Ejemplo

La aplicación puede crear automáticamente:

```python
# Usuarios de ejemplo
- Cliente: test_12345@example.com
- Veterinario: vet@veterinariaclinic.com
- Recepcionista: recep@veterinariaclinic.com

# Mascotas de ejemplo
- Luna (Gato Persa)
- Max (Perro Labrador)
- Bella (Gato Siamés)

# Medicamentos de ejemplo
- Amoxicilina 500mg
- Meloxicam 5mg
- Prednisona 20mg

# Citas de ejemplo
- Consultas generales
- Vacunaciones
- Controles post-operatorios
```

### 4. 📈 Reportes y Análisis

#### Resumen del Sistema
```
📦 Inventario:
  - Total medicamentos: 15
  - Valor total: $125,450.00
  - Stock bajo: 3

📅 Citas hoy: 8
👥 Usuarios activos: 25
🏥 Historias clínicas: 45
```

#### Reportes Detallados
- **HTML**: Reportes visuales con gráficos
- **JSON**: Datos estructurados para análisis
- **CSV**: Exportación para Excel

#### Benchmark de Rendimiento
```
⚡ Auth Service:
  - Promedio: 45.2ms
  - Mínimo: 32.1ms
  - Máximo: 78.5ms
  - Requests exitosos: 10/10
```

## 🔧 Testing Interactivo

### Modo Interactivo por Servicio

#### Auth Service Interactivo
```
🔐 TEST INTERACTIVO - AUTH SERVICE
1. Registrar nuevo usuario
2. Login con usuario existente
3. Verificar token actual
4. Cambiar contraseña
5. Ver perfil actual
```

#### Medical Service Interactivo
```
🏥 TEST INTERACTIVO - MEDICAL SERVICE
1. Crear nueva mascota
2. Buscar mascotas
3. Ver mascota por ID
4. Crear historia clínica
5. Ver historias clínicas de mascota
6. Agregar prescripción
7. Subir resultado de examen
```

#### Inventory Service Interactivo
```
💊 TEST INTERACTIVO - INVENTORY SERVICE
1. Crear nuevo medicamento
2. Buscar medicamentos
3. Ver medicamento por ID
4. Agregar stock
5. Reducir stock
6. Ver movimientos de stock
7. Ver alertas de stock bajo
8. Ver medicamentos por vencer
9. Resumen de inventario
```

## 🛠 Herramientas Avanzadas

### 1. Benchmark de Servicios
- Ejecuta múltiples requests concurrentes
- Mide latencia, throughput y disponibilidad
- Genera reportes de performance

### 2. Test de Conectividad
- Verifica conectividad de red
- Mide timeouts y errores de conexión
- Diagnostica problemas de red

### 3. Generación de Reportes
- Reportes HTML con visualizaciones
- Exportación a múltiples formatos
- Histórico de tests

### 4. Limpieza de Datos
```bash
# Limpia todos los contenedores y volúmenes
make clean
```

## ⚙️ Configuración Avanzada

### Variables de Entorno

```bash
# URLs de servicios (opcional)
export AUTH_SERVICE_URL=http://localhost:5001
export MEDICAL_SERVICE_URL=http://localhost:5004
export INVENTORY_SERVICE_URL=http://localhost:5005
export APPOINTMENT_SERVICE_URL=http://localhost:5002
export NOTIFICATION_SERVICE_URL=http://localhost:5003

# Configuración de timeouts
export REQUEST_TIMEOUT=15

# Directorio de reportes
export REPORTS_DIR=./custom_reports

# Número de iteraciones para benchmarks
export TEST_ITERATIONS=10

# Entorno (development/production)
export FLASK_ENV=development
```

### Configuración Personalizada

Edita `config.py` para personalizar:

```python
class ConsoleConfig:
    # URLs de servicios
    SERVICES = {
        'auth': 'http://localhost:5001',
        'medical': 'http://localhost:5004',
        # ...
    }
    
    # Configuración de testing
    DEFAULT_TEST_ITERATIONS = 5
    REQUEST_TIMEOUT = 10
    
    # Configuración de datos de ejemplo
    SAMPLE_DATA_CONFIG = {
        'create_multiple_users': True,
        'create_multiple_pets': True,
        'user_roles': ['client', 'veterinarian']
    }
```

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. "Docker no está ejecutándose"
```bash
# Verificar Docker
docker --version
docker info

# Iniciar Docker (Ubuntu/Debian)
sudo systemctl start docker

# Iniciar Docker (macOS/Windows)
# Abrir Docker Desktop
```

#### 2. "Servicios no disponibles"
```bash
# Verificar puertos
sudo lsof -i :5001
sudo lsof -i :5432

# Reiniciar servicios
make clean
make dev-up
```

#### 3. "Error de permisos"
```bash
# Dar permisos a scripts
chmod +x run_console.sh
chmod +x ../scripts/*.sh

# Verificar permisos de Docker
sudo usermod -aG docker $USER
```

#### 4. "Módulo no encontrado"
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# Verificar entorno virtual
source venv/bin/activate
which python
```

### Logs de Debugging

#### Ver logs de servicios
```bash
# Desde la aplicación de consola
# Opción 11: Ver logs en tiempo real

# O manualmente
make dev-logs
docker-compose -f ../docker-compose.dev.yml logs -f
```

#### Logs específicos por servicio
```bash
docker logs vet_auth_service_dev
docker logs vet_medical_service_dev
docker logs vet_inventory_service_dev
```

## 📊 Casos de Uso

### 1. Desarrollo de Frontend

```python
# La aplicación de consola simula lo que hará el frontend:
# 1. Login de usuario
login_data = {"email": "user@example.com", "password": "pass123"}
response = requests.post("http://localhost:5001/auth/login", json=login_data)

# 2. Crear mascota
pet_data = {"name": "Luna", "species": "Gato", "owner_id": user_id}
response = requests.post("http://localhost:5004/medical/pets", json=pet_data)

# 3. Agendar cita
appointment_data = {"pet_id": pet_id, "veterinarian_id": vet_id, "date": "2024-12-25"}
response = requests.post("http://localhost:5002/appointments/create", json=appointment_data)
```

### 2. Testing de APIs

```python
# Test automático de endpoints
from utils import APITester

tester = APITester("http://localhost:5001", "auth_service")
result = tester.test_endpoint("POST", "/auth/login", login_data, 200)

if result['success']:
    print("✅ Login exitoso")
else:
    print(f"❌ Login falló: {result['error']}")
```

### 3. Validación de Flujos

```python
# Flujo completo de usuario
1. Registro → Login → Crear mascota → Agendar cita → Recibir notificación
2. Login veterinario → Ver citas → Crear historia clínica → Prescribir medicamento
3. Recepcionista → Facturar consulta → Confirmar pago
```

## 🔄 Flujos de Trabajo

### Flujo de Desarrollo

1. **Inicio**: `./run_console.sh`
2. **Verificar servicios**: Opción 2
3. **Crear datos de ejemplo**: Opción 9
4. **Test específico**: Opciones 4-8
5. **Desarrollo de funcionalidad**
6. **Test completo**: Opción 3
7. **Generar reporte**: Opción 10

### Flujo de Testing

1. **Ejecutar suite completa**: Opción 3
2. **Revisar reportes HTML**: `./reports/`
3. **Identificar fallos**
4. **Test interactivo específico**: Menu interactivo
5. **Corregir y repetir**

### Flujo de CI/CD

```bash
# En script de CI/CD
cd console_app
python3 -c "
from main import VeterinaryConsoleApp
app = VeterinaryConsoleApp()
app.start_services()
success = app.run_complete_tests()
exit(0 if success else 1)
"
```

## 📝 Ejemplos de Comandos

### Comandos Rápidos

```bash
# Inicio completo
./run_console.sh

# Solo verificar servicios
python3 -c "
from main import VeterinaryConsoleApp
app = VeterinaryConsoleApp()
app.check_docker_services()
"

# Test específico de auth
python3 -c "
from main import VeterinaryConsoleApp
app = VeterinaryConsoleApp()
app.test_auth_service()
"

# Generar reporte
python3 -c "
from main import VeterinaryConsoleApp
app = VeterinaryConsoleApp()
app.generate_complete_report()
"
```

## 🤝 Contribución

### Agregar Nuevos Tests

1. **Editar `main.py`**: Agregar método de test
2. **Actualizar menú**: Agregar opción al menú principal
3. **Documentar**: Actualizar este README

### Agregar Nuevos Servicios

1. **Editar `config.py`**: Agregar URL del servicio
2. **Crear tests**: Implementar métodos de testing
3. **Actualizar utilidades**: Modificar `utils.py` si es necesario

## 📚 Referencias

### APIs de Microservicios

- **Auth Service**: `http://localhost:5001/health`
- **Medical Service**: `http://localhost:5004/health`
- **Inventory Service**: `http://localhost:5005/health`
- **Appointment Service**: `http://localhost:5002/health`
- **Notification Service**: `http://localhost:5003/health`

### Documentación Relacionada

- [README Principal del Proyecto](../README.md)
- [Documentación de Microservicios](../docs/)
- [Guía de Deployment](../docs/deployment.md)

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](../LICENSE) para más detalles.

---

## 🎯 Próximos Pasos

1. **Ejecutar la aplicación**: `./run_console.sh`
2. **Familiarizarte con el menú principal**
3. **Crear datos de ejemplo**: Opción 9
4. **Ejecutar tests completos**: Opción 3
5. **Explorar testing interactivo**
6. **Generar tu primer reporte**

¡Listo para empezar! 🚀