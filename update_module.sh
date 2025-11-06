#!/bin/bash

# Script to update the pos_delivery module in Odoo
# Run this after creating your database

echo "Updating pos_delivery module in Odoo..."
docker exec -it insotech-web-1 odoo -d odoo -u pos_delivery --stop-after-init

echo ""
echo "Module updated successfully!"
echo "If you already had a database, the changes should now be applied."
echo ""
echo "To restart Odoo in normal mode, run:"
echo "docker compose restart web"

