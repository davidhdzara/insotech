#!/bin/bash

# Quick setup script for invoice customization
# This script helps you apply the invoice customization after database creation

echo "=========================================="
echo "  PERSONALIZACIÓN DE FACTURAS POS - ODOO"
echo "=========================================="
echo ""

# Check if container is running
if ! docker ps | grep -q insotech-web-1; then
    echo "⚠️  El contenedor de Odoo no está corriendo."
    echo "   Iniciando contenedores..."
    cd /home/jeff/Documents/insotech-repo/insotech
    docker compose up -d
    echo "   Esperando 10 segundos para que Odoo inicie..."
    sleep 10
fi

echo "✅ Contenedor de Odoo está corriendo"
echo ""
echo "📋 PASOS SIGUIENTES:"
echo ""
echo "1. Accede a Odoo:"
echo "   http://localhost:8069"
echo ""
echo "2. Si es primera vez:"
echo "   - Crea una nueva base de datos"
echo "   - Nombre sugerido: 'odoo'"
echo "   - Instala los módulos necesarios:"
echo "     * Point of Sale"
echo "     * Gestión de Entregas POS"
echo ""
echo "3. Si ya tienes una base de datos:"
echo "   - Actualiza el módulo ejecutando:"
echo "     ./update_module.sh"
echo ""
echo "4. Para probar la personalización:"
echo "   - Ve a Point of Sale"
echo "   - Crea una orden con un cliente"
echo "   - Asegúrate de que el cliente tenga:"
echo "     • Nombre"
echo "     • Dirección"
echo "     • Teléfono"
echo "   - Genera la factura"
echo "   - La factura mostrará toda la información del cliente"
echo ""
echo "=========================================="
echo ""

# Show container status
echo "📊 ESTADO DE CONTENEDORES:"
docker ps --filter name=insotech --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "Para más información, consulta:"
echo "  pos_delivery/INVOICE_CUSTOMIZATION.md"
echo ""

