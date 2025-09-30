# -*- coding: utf-8 -*-
{
    'name': "Test Module",

    'summary': """
        Simple test module for Odoo.sh validation""",

    'description': """
        A minimal test module to verify Odoo.sh is working correctly
    """,

    'author': "Insotech",
    'website': "http://www.insotech.com",

    'category': 'Tools',
    'version': '1.0',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}