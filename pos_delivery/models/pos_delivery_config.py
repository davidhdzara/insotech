# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosDeliveryConfig(models.Model):
    _name = 'pos.delivery.config'
    _description = 'Configuración de Entregas POS'

    name = fields.Char(string='Nombre de Configuración', default='Configuración de Entregas')
    
    # Feature Toggles
    enable_photo_required = fields.Boolean(
        string='Requerir Foto de Entrega',
        default=False,
        help="Hacer obligatoria la carga de foto al completar entregas"
    )
    enable_signature_required = fields.Boolean(
        string='Requerir Firma del Cliente',
        default=False,
        help="Hacer obligatoria la firma del cliente al completar entregas"
    )
    enable_geolocation = fields.Boolean(
        string='Habilitar Geolocalización',
        default=True,
        help="Permitir rastrear la ubicación de entrega con coordenadas GPS"
    )
    enable_zone_required = fields.Boolean(
        string='Requerir Zona de Entrega',
        default=True,
        help="Hacer obligatoria la selección de zona de entrega"
    )
    enable_rating = fields.Boolean(
        string='Habilitar Calificación del Cliente',
        default=True,
        help="Permitir a los clientes calificar el servicio de entrega"
    )
    
    # Auto-assignment Settings
    enable_auto_assignment = fields.Boolean(
        string='Habilitar Asignación Automática',
        default=False,
        help="Asignar automáticamente entregas a repartidores disponibles"
    )
    
    # Time Settings
    default_delivery_time = fields.Integer(
        string='Tiempo de Entrega Predeterminado (minutos)',
        default=30,
        help="Tiempo de entrega estimado predeterminado si no se establece la zona"
    )
    
    # Notification Settings
    enable_notifications = fields.Boolean(
        string='Habilitar Notificaciones',
        default=True,
        help="Enviar notificaciones en cambios de estado"
    )
    
    # Map Settings
    default_map_zoom = fields.Integer(
        string='Nivel de Zoom del Mapa Predeterminado',
        default=15,
        help="Nivel de zoom predeterminado para mapas (1-20)"
    )
    
    company_id = fields.Many2one('res.company', string='Compañía', 
                                  default=lambda self: self.env.company)
    
    server_url = fields.Char(
        string='URL del Servidor',
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
            config = self.create({'name': 'Configuración de Entregas'})
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

