# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosDeliveryConfig(models.Model):
    _name = 'pos.delivery.config'
    _description = 'POS Delivery Configuration'

    name = fields.Char(string='Configuration Name', default='Delivery Settings')
    
    # Feature Toggles
    enable_photo_required = fields.Boolean(
        string='Require Delivery Photo',
        default=False,
        help="Make photo upload mandatory when completing deliveries"
    )
    enable_signature_required = fields.Boolean(
        string='Require Customer Signature',
        default=False,
        help="Make customer signature mandatory when completing deliveries"
    )
    enable_geolocation = fields.Boolean(
        string='Enable Geolocation',
        default=True,
        help="Allow tracking delivery location with GPS coordinates"
    )
    enable_zone_required = fields.Boolean(
        string='Require Delivery Zone',
        default=True,
        help="Make delivery zone selection mandatory"
    )
    enable_rating = fields.Boolean(
        string='Enable Customer Rating',
        default=True,
        help="Allow customers to rate delivery service"
    )
    
    # Auto-assignment Settings
    enable_auto_assignment = fields.Boolean(
        string='Enable Auto-Assignment',
        default=False,
        help="Automatically assign deliveries to available delivery persons"
    )
    
    # Time Settings
    default_delivery_time = fields.Integer(
        string='Default Delivery Time (minutes)',
        default=30,
        help="Default estimated delivery time if zone is not set"
    )
    
    # Notification Settings
    enable_notifications = fields.Boolean(
        string='Enable Notifications',
        default=True,
        help="Send notifications on status changes"
    )
    
    # Map Settings
    default_map_zoom = fields.Integer(
        string='Default Map Zoom Level',
        default=15,
        help="Default zoom level for maps (1-20)"
    )
    
    company_id = fields.Many2one('res.company', string='Company', 
                                  default=lambda self: self.env.company)

    @api.model
    def get_config(self):
        """Get current configuration"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({'name': 'Delivery Settings'})
        return config

