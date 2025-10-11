# -*- coding: utf-8 -*-
{
    'name': "POS Delivery Management",
    'summary': "Advanced delivery order management integrated with Point of Sale",
    'description': """
        Complete delivery management system for POS orders
        ====================================================
        
        Features:
        ---------
        * Create delivery orders directly from POS
        * Assign delivery to portal users (no license consumption)
        * Track delivery status with kanban view
        * Delivery person and warehouse comments
        * Photo evidence of delivery
        * Customer rating system
        * Automatic timers and notifications
        * Delivery zones and priority management
        * Performance statistics per delivery person
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
        'views/pos_order_views.xml',
        'views/res_partner_views.xml',
        'views/delivery_person_views.xml',
        'views/delivery_history_views.xml',
        'views/delivery_geolocation_views.xml',
        'views/delivery_config_views.xml',
        'views/delivery_app_config_views.xml',
        'wizard/delivery_app_qr_wizard_views.xml',
        'views/pos_delivery_menus.xml',
    ],
    'external_dependencies': {
        'python': ['qrcode'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

