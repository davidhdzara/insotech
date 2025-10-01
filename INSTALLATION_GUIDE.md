# Guía de Instalación - Módulos Odoo 18

## 📦 Módulos Incluidos

1. **pos** - Módulo de prueba simple
2. **pos_delivery** - Sistema completo de gestión de domicilios para POS

## 🚀 Instalación con Docker (Recomendado)

### 1. Iniciar Odoo

```bash
cd /home/jeff/Documents/insotech
docker-compose up
```

Espera a que aparezca el mensaje:
```
odoo-web-1  | INFO ? odoo: HTTP service (werkzeug) running on...
```

### 2. Configurar Base de Datos

1. Abre tu navegador en: http://localhost:8069
2. Configuración de base de datos:
   - **Master password**: admin
   - **Database name**: production
   - **Email**: tu correo
   - **Password**: tu contraseña
   - **Language**: Spanish / Español
   - **Country**: Colombia (o tu país)
   - Desmarca "Load demonstration data" para producción
3. Click en "Create database"

### 3. Instalar Módulos

#### A. Instalar Point of Sale (POS)

1. Ve a **Apps** (Aplicaciones)
2. Busca "Point of Sale"
3. Click en **Install**
4. Espera a que termine la instalación

#### B. Instalar POS Delivery Management

1. Ve a **Apps** (Aplicaciones)
2. Remueve el filtro "Apps" (click en la X)
3. Busca "POS Delivery Management"
4. Click en **Install**
5. Espera a que termine la instalación

### 4. Configuración Inicial

#### Crear Personas de Domicilio

1. Ve a **Deliveries → Delivery Persons**
2. Click en **Create**
3. Llena los datos:
   - Nombre del domiciliario
   - Teléfono
   - Tipo de vehículo
   - Placa del vehículo
4. **Importante**: En la pestaña de usuario, crear un usuario Portal:
   - Click en "Create User"
   - Tipo de usuario: **Portal**
   - Esto NO consume licencia ✅
5. Guardar

#### Configurar Zonas de Entrega

1. Ve a **Deliveries → Configuration → Delivery Zones**
2. Edita las zonas preconfiguradas (North, South, East, West, Center) o crea nuevas
3. Ajusta:
   - Costo de domicilio
   - Tiempo estimado
   - Descripción

### Configurar Funcionalidades Avanzadas

1. Ve a **Deliveries → Configuration → Settings**
2. Activa/desactiva según necesites:
   - ✅ **Require Delivery Photo**: Obliga foto al completar
   - ✅ **Require Customer Signature**: Obliga firma al completar
   - ✅ **Enable Geolocation**: Permite tracking GPS
   - ✅ **Require Delivery Zone**: Obliga seleccionar zona
   - ✅ **Enable Customer Rating**: Permite calificaciones
   - ✅ **Enable Notifications**: Notificaciones automáticas

## 📱 Uso del Sistema

### Crear un Domicilio desde POS

1. Crea o abre una orden en **Point of Sale → Orders**
2. En la vista de la orden, verás un botón **"Create Delivery"** (🏍️)
3. Click en el botón
4. Completa la información:
   - Dirección de entrega
   - Teléfono
   - Zona de entrega
   - Prioridad
   - Asignar domiciliario (opcional)
5. Guardar

### Gestionar Domicilios (Vista Kanban)

1. Ve a **Deliveries → Delivery Orders**
2. Verás el tablero Kanban con 5 columnas:
   - **Pending**: Pendiente de asignar
   - **Assigned**: Asignado a domiciliario
   - **In Transit**: En camino
   - **Completed**: Completado
   - **Failed**: Fallido

3. **Acciones rápidas**:
   - Click en "Assign" para asignar
   - Click en "Start Delivery" cuando salga
   - Click en "Complete" cuando entregue
   - Arrastra entre columnas (limitado por workflow)

### Portal del Domiciliario

Los domiciliarios pueden:
1. Iniciar sesión en http://localhost:8069
2. Ver sus domicilios asignados
3. Ver detalles del cliente y orden
4. Agregar notas
5. Subir foto de evidencia
6. Marcar como completado/fallido

## 🔧 Comandos Útiles

### Reiniciar Odoo
```bash
docker-compose restart web
```

### Ver logs
```bash
docker-compose logs -f web
```

### Detener todo
```bash
docker-compose down
```

### Detener y eliminar datos (CUIDADO!)
```bash
docker-compose down -v
```

## 📊 Características Destacadas

### ✅ Sin Consumo de Licencias
Los domiciliarios usan usuarios **Portal** que NO consumen licencias de Odoo.

### ✅ UX/UI Optimizado
- Vista Kanban con drag & drop
- Badges de colores por prioridad
- Timer automático
- Estadísticas en tiempo real
- Diseño responsive

### ✅ Trazabilidad Completa
- Comentarios de bodega
- Comentarios de domiciliario
- Foto de evidencia
- Firma del cliente
- Rating del servicio

### ✅ Estadísticas por Domiciliario
- Total de entregas
- Promedio de calificación
- Tiempo promedio de entrega
- Entregas exitosas vs fallidas

### ✅ Gestión de Zonas
- Costos diferenciados
- Tiempos estimados
- Estadísticas por zona

## 🎯 Mejores Prácticas

1. **Siempre asignar zona** para obtener costos y tiempos precisos
2. **Usar prioridades** para órdenes urgentes
3. **Solicitar foto de evidencia** en todas las entregas
4. **Monitorear estadísticas** de domiciliarios regularmente
5. **Revisar domicilios fallidos** para identificar patrones

## ❓ Solución de Problemas

### El módulo no aparece en Apps
- Actualiza la lista de aplicaciones
- Verifica que el módulo esté en `/mnt/extra-addons/`
- Revisa los logs: `docker-compose logs web`

### Error al instalar
- Verifica que Point of Sale esté instalado primero
- Reinicia el contenedor: `docker-compose restart web`

### Cambios no se reflejan
- Reinicia Odoo: `docker-compose restart web`
- Actualiza el módulo desde Apps

## 🚀 Subir a Odoo.sh

1. Sube los directorios `pos` y `pos_delivery` a tu repositorio Git
2. Push a la rama de Odoo.sh
3. Espera el despliegue automático
4. Instala los módulos desde la interfaz de Odoo.sh

## 📞 Soporte

Para problemas o preguntas, contacta al equipo de desarrollo.

---

**Desarrollado por Insotech** 🚀

