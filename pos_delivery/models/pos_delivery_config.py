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
    
    server_url = fields.Char(
        string='Server URL',
        compute='_compute_server_url',
        help='URL del servidor Odoo para configurar la app'
    )

    @api.depends('company_id')
    def _compute_server_url(self):
        """Compute server URL from system parameter"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.server_url = base_url

    @api.model
    def get_config(self):
        """Get current configuration"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({'name': 'Delivery Settings'})
        return config

    def action_show_qr_code(self):
        """Show QR code for app configuration"""
        self.ensure_one()
        
        import json
        import qrcode
        import base64
        from io import BytesIO
        
        # Create config data
        config_data = {
            'server_url': self.server_url,
            'api_version': '1.0',
            'configured_at': fields.Datetime.now().isoformat()
        }
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(config_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_image = base64.b64encode(buffer.getvalue()).decode()
        
        # Create wizard to show QR
        wizard = self.env['delivery.app.qr.wizard'].create({
            'qr_image': qr_image,
            'config_json': json.dumps(config_data, indent=2),
            'server_url': self.server_url
        })
        
        return {
            'name': 'Código QR - Configuración App',
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.app.qr.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

