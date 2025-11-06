# Personalización de Facturas POS

## Cambios Implementados

Se ha personalizado la factura generada por el POS de Odoo para incluir la siguiente información del cliente:

1. **Nombre completo del cliente**
2. **Dirección completa** (calle, calle 2, ciudad, estado, código postal, país)
3. **Teléfono** (teléfono fijo y/o móvil)

## Archivos Modificados

### 1. `/pos_delivery/reports/pos_invoice_report.xml`
- **Nuevo archivo** que contiene las plantillas personalizadas para los reportes
- Define tres plantillas:
  - `report_invoice_document_custom`: Personaliza el documento de factura estándar
  - `report_pos_invoice_custom`: Aplica la personalización a facturas POS
  - `pos_receipt_custom`: Personaliza el ticket/recibo del POS

### 2. `/pos_delivery/__manifest__.py`
- Actualizado para incluir el nuevo archivo de reportes en la sección `data`

## Cómo Aplicar los Cambios

### Primera Vez (Base de Datos Nueva)

1. Accede a Odoo en http://localhost:8069
2. Crea una nueva base de datos
3. Instala los módulos necesarios:
   - Point of Sale (pos)
   - Gestión de Entregas POS (pos_delivery)

### Actualizando Módulo (Base de Datos Existente)

Si ya tienes una base de datos creada, ejecuta:

```bash
cd /home/jeff/Documents/insotech-repo/insotech
./update_module.sh
```

O manualmente:

```bash
docker exec -it insotech-web-1 odoo -d odoo -u pos_delivery --stop-after-init
docker compose restart web
```

## Cómo Funciona

### Facturas Normales (account.move)

Cuando se genera una factura desde el backend de Odoo:
- Se hereda la plantilla `account.report_invoice_document`
- Se reemplaza el bloque de dirección con información más detallada
- Muestra nombre, dirección completa y teléfono(s) del cliente

### Recibos/Tickets del POS

Cuando se imprime un ticket desde el POS:
- Se hereda la plantilla `point_of_sale.pos_ticket_without_layout`
- Se agrega una sección "INFORMACIÓN DEL CLIENTE" al final del ticket
- Muestra nombre, dirección y teléfono del cliente seleccionado

## Campos Mostrados

La personalización muestra los siguientes campos del cliente (partner):

- `name`: Nombre del cliente
- `street`: Calle principal
- `street2`: Calle secundaria (opcional)
- `city`: Ciudad
- `state_id`: Estado/Provincia
- `zip`: Código postal
- `country_id`: País
- `phone`: Teléfono fijo
- `mobile`: Teléfono móvil
- `vat`: RFC/NIT/Tax ID (si está disponible)

## Notas Importantes

1. **Información del cliente requerida**: Para que aparezca la información en la factura, el cliente debe estar seleccionado en la orden POS.

2. **Campos opcionales**: Si un campo no está completado en el cliente, simplemente no se mostrará en el reporte.

3. **Compatibilidad**: Esta personalización es compatible con:
   - Odoo 18.0
   - Módulo Point of Sale
   - Módulo Account (facturación)

4. **Personalización adicional**: Si necesitas modificar el diseño o agregar más campos, edita el archivo `pos_invoice_report.xml` en la carpeta `reports/`.

## Soporte

Para más información o soporte, contacta al equipo de desarrollo de Insotech.

