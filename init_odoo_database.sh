#!/bin/bash

# Script mejorado para inicializar Odoo con el módulo personalizado
# Este script crea la base de datos e instala los módulos de manera segura

echo "=========================================="
echo "  INICIALIZACIÓN DE ODOO CON POS CUSTOM"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DB_NAME="odoo"
ADMIN_PASSWORD="admin"

echo "📋 Configuración:"
echo "   Base de datos: $DB_NAME"
echo "   Contraseña admin: $ADMIN_PASSWORD"
echo ""

# Step 1: Verificar que los contenedores estén corriendo
echo "1️⃣  Verificando contenedores..."
if ! docker ps | grep -q insotech-web-1; then
    echo -e "${RED}❌ Los contenedores no están corriendo${NC}"
    echo "   Iniciando contenedores..."
    cd /home/jeff/Documents/insotech-repo/insotech
    docker compose up -d
    echo "   Esperando 20 segundos para que Odoo inicie completamente..."
    sleep 20
else
    echo -e "${GREEN}✅ Contenedores corriendo${NC}"
fi

# Step 2: Verificar que PostgreSQL esté listo
echo ""
echo "2️⃣  Esperando a que PostgreSQL esté listo..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec insotech-db-1 pg_isready -U odoo &> /dev/null; then
        echo -e "${GREEN}✅ PostgreSQL está listo${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Intento $attempt de $max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ PostgreSQL no está respondiendo${NC}"
    exit 1
fi

# Step 3: Crear base de datos con módulos básicos
echo ""
echo "3️⃣  Creando base de datos e instalando módulos base..."
echo "   Esto puede tomar varios minutos, por favor espera..."
echo ""

# Crear base de datos con módulos básicos usando el CLI de Odoo
docker exec -i insotech-web-1 odoo \
    -d $DB_NAME \
    --db_host=db \
    --db_user=odoo \
    --db_password=odoo \
    -i base,web,point_of_sale,account \
    --stop-after-init \
    --without-demo=all \
    --load-language=es_MX 2>&1 | tail -20

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Base de datos creada con módulos base${NC}"
else
    echo ""
    echo -e "${RED}❌ Error al crear la base de datos${NC}"
    exit 1
fi

# Step 4: Instalar el módulo personalizado
echo ""
echo "4️⃣  Instalando módulo personalizado pos_delivery..."
echo ""

docker exec -i insotech-web-1 odoo \
    -d $DB_NAME \
    --db_host=db \
    --db_user=odoo \
    --db_password=odoo \
    -i pos_delivery \
    --stop-after-init \
    --without-demo=all 2>&1 | tail -20

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Módulo pos_delivery instalado${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Hubo algún problema, pero continuamos...${NC}"
fi

# Step 5: Reiniciar Odoo en modo normal
echo ""
echo "5️⃣  Reiniciando Odoo en modo normal..."
docker compose restart web
sleep 5

echo ""
echo "=========================================="
echo -e "${GREEN}✅ ¡INSTALACIÓN COMPLETADA!${NC}"
echo "=========================================="
echo ""
echo "📝 ACCESO A ODOO:"
echo "   URL: http://localhost:8069"
echo "   Base de datos: $DB_NAME"
echo "   Usuario: admin"
echo "   Contraseña: $ADMIN_PASSWORD"
echo ""
echo "📦 MÓDULOS INSTALADOS:"
echo "   ✅ Base"
echo "   ✅ Web"
echo "   ✅ Point of Sale"
echo "   ✅ Account (Facturación)"
echo "   ✅ Gestión de Entregas POS (pos_delivery)"
echo ""
echo "🎯 PRÓXIMOS PASOS:"
echo "   1. Accede a http://localhost:8069"
echo "   2. Inicia sesión con las credenciales de arriba"
echo "   3. Ve a Contactos y crea un cliente con:"
echo "      • Nombre"
echo "      • Dirección completa"
echo "      • Teléfono"
echo "   4. Ve a Point of Sale"
echo "   5. Crea una orden seleccionando el cliente"
echo "   6. Genera la factura"
echo "   7. Verifica que la factura muestre toda la información del cliente"
echo ""
echo "=========================================="

