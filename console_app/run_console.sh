#!/bin/bash
# console_app/run_console.sh

# Script para ejecutar la aplicación de consola del sistema veterinario

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐾 Sistema de Gestión Veterinaria - Aplicación de Consola${NC}"
echo -e "${BLUE}================================================================${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra main.py en el directorio actual${NC}"
    echo -e "${YELLOW}💡 Asegúrate de ejecutar este script desde console_app/${NC}"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 encontrado${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    echo -e "${YELLOW}💡 Instala Docker para usar todas las funcionalidades${NC}"
fi

# Verificar docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️ docker-compose no encontrado, intentando con docker compose${NC}"
fi

# Verificar make
if ! command -v make &> /dev/null; then
    echo -e "${YELLOW}⚠️ make no encontrado, usando docker-compose directamente${NC}"
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual
echo -e "${BLUE}🔄 Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${BLUE}📚 Instalando dependencias...${NC}"
pip install -r requirements.txt

# Verificar estructura del proyecto padre
if [ ! -f "../docker-compose.dev.yml" ]; then
    echo -e "${YELLOW}⚠️ No se encuentra docker-compose.dev.yml en el directorio padre${NC}"
    echo -e "${YELLOW}💡 Asegúrate de que la estructura del proyecto esté completa${NC}"
fi

echo -e "${GREEN}🚀 Iniciando aplicación de consola...${NC}"
echo -e "${BLUE}================================================================${NC}"

# Ejecutar la aplicación
python3 main.py

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}👋 ¡Gracias por usar el sistema de testing!${NC}"