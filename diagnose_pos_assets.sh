#!/bin/bash

echo "==================================="
echo "  DIAGNÓSTICO DE ASSETS DEL POS"
echo "==================================="
echo ""

echo "1. Verificando archivos en el módulo:"
echo "--------------------------------------"
ls -la /home/jeff/Documents/insotech-repo/insotech/pos_delivery/static/src/js/
ls -la /home/jeff/Documents/insotech-repo/insotech/pos_delivery/static/src/xml/

echo ""
echo "2. Verificando que los archivos estén montados en el contenedor:"
echo "----------------------------------------------------------------"
docker exec insotech-web-1 ls -la /mnt/extra-addons/pos_delivery/static/src/js/
docker exec insotech-web-1 ls -la /mnt/extra-addons/pos_delivery/static/src/xml/

echo ""
echo "3. Contenido del manifiesto (assets):"
echo "--------------------------------------"
docker exec insotech-web-1 grep -A 10 "assets" /mnt/extra-addons/pos_delivery/__manifest__.py

echo ""
echo "4. Verificando logs recientes de assets:"
echo "-----------------------------------------"
docker logs insotech-web-1 2>&1 | grep -i "point_of_sale.*assets\|pos_delivery" | tail -10

echo ""
echo "INSTRUCCIONES:"
echo "==================================="
echo "1. Abre el POS en tu navegador"
echo "2. Presiona F12 para abrir la consola"
echo "3. Ve a la pestaña 'Console'"
echo "4. Busca errores en rojo relacionados con 'pos_delivery' o 'models.js'"
echo "5. Comparte cualquier error que veas"
echo ""

