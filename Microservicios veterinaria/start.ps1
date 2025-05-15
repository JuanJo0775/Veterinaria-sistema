# start.ps1 - Script de inicio para Windows PowerShell

# Colores para output
$RED = "Red"
$GREEN = "Green"
$YELLOW = "Yellow"

Write-Host "🚀 Iniciando Sistema de Citas Veterinarias..." -ForegroundColor $GREEN

# Verificar si Docker está instalado
try {
    docker --version | Out-Null
    Write-Host "✅ Docker está instalado" -ForegroundColor $GREEN
} catch {
    Write-Host "❌ Docker no está instalado. Por favor instala Docker Desktop primero." -ForegroundColor $RED
    exit 1
}

# Verificar si Docker Compose está instalado
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose está instalado" -ForegroundColor $GREEN
} catch {
    Write-Host "❌ Docker Compose no está instalado." -ForegroundColor $RED
    exit 1
}

# Crear archivo .env si no existe
if (!(Test-Path .env)) {
    Write-Host "📝 Creando archivo .env..." -ForegroundColor $YELLOW
    @"
# Database Configuration
DB_USER=postgres
DB_PASSWORD=bocato0731
DB_NAME=veterinary-appointment-system

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this

# Email Configuration (opcional para desarrollo)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Service URLs
AUTH_SERVICE_URL=http://auth-service:5001
APPOINTMENT_SERVICE_URL=http://appointment-service:5002
NOTIFICATION_SERVICE_URL=http://notification-service:5003
"@ | Out-File -FilePath .env -Encoding UTF8
}

# Verificar parámetros
$clean = $false
if ($args[0] -eq "--clean") {
    $clean = $true
}

# Detener servicios anteriores
Write-Host "🛑 Deteniendo servicios anteriores..." -ForegroundColor $YELLOW
docker-compose down

# Limpiar volúmenes si se especifica
if ($clean) {
    Write-Host "🧹 Limpiando volúmenes..." -ForegroundColor $YELLOW
    docker-compose down -v
}

# Construir imágenes
Write-Host "🔨 Construyendo imágenes..." -ForegroundColor $GREEN
docker-compose build

# Levantar servicios
Write-Host "🚀 Levantando servicios..." -ForegroundColor $GREEN
docker-compose up -d

# Esperar a que los servicios estén listos
Write-Host "⏳ Esperando a que los servicios estén listos..." -ForegroundColor $YELLOW
Start-Sleep -Seconds 15

# Verificar estado de los servicios
Write-Host "✅ Verificando servicios..." -ForegroundColor $GREEN
docker-compose ps

Write-Host ""
Write-Host "✅ Sistema listo!" -ForegroundColor $GREEN
Write-Host "🌐 Frontend: http://localhost:5000" -ForegroundColor $GREEN
Write-Host "🔐 Auth Service: http://localhost:5001/health" -ForegroundColor $GREEN
Write-Host "📅 Appointment Service: http://localhost:5002/health" -ForegroundColor $GREEN
Write-Host "📧 Notification Service: http://localhost:5003/health" -ForegroundColor $GREEN
Write-Host ""
Write-Host "Para ver los logs: docker-compose logs -f" -ForegroundColor $YELLOW
Write-Host "Para detener: docker-compose down" -ForegroundColor $YELLOW