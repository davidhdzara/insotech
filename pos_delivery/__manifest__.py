# -*- coding: utf-8 -*-
{
    'name': "Gestión de Entregas POS",
    'summary': "Sistema avanzado de gestión de pedidos de entrega integrado con el Punto de Venta",
    'description': """
        Sistema completo de gestión de entregas para órdenes POS
        =========================================================
        
        Características:
        ----------------
        * Crear órdenes de entrega directamente desde el POS
        * Asignar entregas a usuarios del portal (sin consumo de licencias)
        * Seguimiento del estado de entregas con vista kanban
        * Comentarios del repartidor y del almacén
        * Evidencia fotográfica de la entrega
        * Sistema de calificación del cliente
        * Temporizadores automáticos y notificaciones
        * Gestión de zonas de entrega y prioridades
        * Estadísticas de rendimiento por repartidor
    """,
    'author': "Insotech",
    'website': "http://www.insotech.com",
    'category': 'Point of Sale',
    'version': '1.0',
    'depends': ['base', 'point_of_sale', 'portal'],
    'data': [
        'security/pos_delivery_security.xml',
        'security/ir.model.access.csv',
        'data/delivery_zones_data.xml',
        'views/pos_config_views.xml',
        'views/pos_delivery_order_views.xml',
        'views/pos_delivery_stage_time_views.xml',
        'views/pos_order_views.xml',
        'views/res_partner_views.xml',
        'views/delivery_person_views.xml',
        'views/delivery_history_views.xml',
        'views/delivery_geolocation_views.xml',
        'views/delivery_config_views.xml',
        'wizard/delivery_app_qr_wizard_views.xml',
        'views/delivery_app_config_views.xml',
        'views/pos_delivery_menus.xml',  # Load menus LAST, after all actions are defined
    ],
    'external_dependencies': {
        'python': ['qrcode'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

