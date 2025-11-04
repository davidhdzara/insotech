# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Delivery Person Fields
    is_delivery_person = fields.Boolean(string='Es Repartidor', default=False)
    delivery_person_code = fields.Char(string='Código de Repartidor')
    vehicle_type = fields.Selection([
        ('motorcycle', 'Moto')
    ], string='Tipo de Vehículo', default='motorcycle')
    vehicle_plate = fields.Char(string='Placa del Vehículo')
    
    # Documentation Fields
    document_type = fields.Selection([
        ('cc', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('ti', 'Tarjeta de Identidad'),
        ('passport', 'Pasaporte'),
        ('other', 'Otro')
    ], string='Tipo de Documento')
    document_number = fields.Char(string='Número de Documento')
    document_expedition_date = fields.Date(string='Fecha de Expedición')
    document_expiry_date = fields.Date(string='Vigencia')
    
    # Connection tracking
    last_connection = fields.Datetime(string='Última Conexión', readonly=True,
                                      help="Última vez que el repartidor se conectó a la app",
                                      copy=False, default=False)
    last_connection_display = fields.Char(string='Última Conexión', 
                                          compute='_compute_last_connection_display',
                                          help="Formato legible de la última conexión", store=False)
    is_online = fields.Boolean(string='En Línea', compute='_compute_is_online',
                               help="Conectado en los últimos 5 minutos", store=False)
    
    # Statistics
    total_deliveries = fields.Integer(string='Total de Entregas', compute='_compute_delivery_stats')
    completed_deliveries = fields.Integer(string='Entregas Completadas', 
                                          compute='_compute_delivery_stats')
    failed_deliveries = fields.Integer(string='Entregas Fallidas', compute='_compute_delivery_stats')
    avg_delivery_time = fields.Float(string='Tiempo Promedio de Entrega (min)', 
                                      compute='_compute_delivery_stats')
    
    @api.constrains('email', 'is_delivery_person')
    def _check_delivery_person_email(self):
        """Validate that delivery person has a valid email"""
        for partner in self:
            if partner.is_delivery_person:
                if not partner.email:
                    raise models.ValidationError(_('El domiciliario debe tener un correo electrónico.'))
                # Basic email validation
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, partner.email):
                    raise models.ValidationError(_('El correo electrónico no es válido.'))

    def _compute_delivery_stats(self):
        """Compute delivery statistics for each delivery person"""
        for partner in self:
            if partner.is_delivery_person:
                deliveries = self.env['pos.delivery.order'].search([
                    ('delivery_person_id', '=', partner.id)
                ])
                
                partner.total_deliveries = len(deliveries)
                partner.completed_deliveries = len(deliveries.filtered(lambda d: d.state == 'completed'))
                partner.failed_deliveries = len(deliveries.filtered(lambda d: d.state == 'failed'))
                
                # Calculate average delivery time
                completed = deliveries.filtered(lambda d: d.state == 'completed' and d.total_delivery_time > 0)
                if completed:
                    partner.avg_delivery_time = sum(completed.mapped('total_delivery_time')) / len(completed)
                else:
                    partner.avg_delivery_time = 0
            else:
                partner.total_deliveries = 0
                partner.completed_deliveries = 0
                partner.failed_deliveries = 0
                partner.avg_delivery_time = 0
    
    @api.depends('last_connection')
    def _compute_last_connection_display(self):
        """Format last connection time in a human readable way"""
        from datetime import datetime, timedelta
        
        for partner in self:
            if not partner.last_connection:
                partner.last_connection_display = 'Nunca'
                continue
            
            now = fields.Datetime.now()
            delta = now - partner.last_connection
            
            # Calculate time difference
            seconds = int(delta.total_seconds())
            minutes = seconds // 60
            hours = minutes // 60
            days = hours // 24
            
            if seconds < 60:
                partner.last_connection_display = 'Justo ahora'
            elif minutes < 60:
                partner.last_connection_display = f'Hace {minutes} minuto{"s" if minutes > 1 else ""}'
            elif hours < 24:
                partner.last_connection_display = f'Hace {hours} hora{"s" if hours > 1 else ""}'
            elif days < 7:
                partner.last_connection_display = f'Hace {days} día{"s" if days > 1 else ""}'
            else:
                # Show date for older connections
                partner.last_connection_display = partner.last_connection.strftime('%d/%m/%Y %H:%M')
    
    @api.depends('last_connection')
    def _compute_is_online(self):
        """Check if delivery person is online (connected in last 5 minutes)"""
        from datetime import timedelta
        
        for partner in self:
            if partner.last_connection:
                now = fields.Datetime.now()
                delta = now - partner.last_connection
                # Consider online if connected in the last 5 minutes
                partner.is_online = delta.total_seconds() < 300
            else:
                partner.is_online = False

    def action_view_deliveries(self):
        """View all deliveries for this person"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mis Entregas'),
            'res_model': 'pos.delivery.order',
            'view_mode': 'list,kanban,form',
            'domain': [('delivery_person_id', '=', self.id)],
            'context': {'default_delivery_person_id': self.id}
        }

