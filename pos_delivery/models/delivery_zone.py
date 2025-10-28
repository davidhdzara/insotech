# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeliveryZone(models.Model):
    _name = 'delivery.zone'
    _description = 'Zona de Entrega'
    _order = 'name'

    name = fields.Char(string='Nombre de Zona', required=True)
    code = fields.Char(string='Código de Zona', required=True)
    delivery_cost = fields.Monetary(string='Costo de Envío', currency_field='currency_id')
    estimated_time = fields.Integer(string='Tiempo Estimado (minutos)', 
                                     help="Tiempo promedio de entrega para esta zona")
    active = fields.Boolean(string='Activo', default=True)
    description = fields.Text(string='Descripción')
    currency_id = fields.Many2one('res.currency', string='Moneda', 
                                   default=lambda self: self.env.company.currency_id)
    
    # Statistics
    delivery_count = fields.Integer(string='Total de Entregas', compute='_compute_statistics')
    avg_delivery_time = fields.Float(string='Tiempo Promedio de Entrega (min)', 
                                      compute='_compute_statistics')

    def _compute_statistics(self):
        """Compute delivery statistics for each zone"""
        for zone in self:
            deliveries = self.env['pos.delivery.order'].search([
                ('delivery_zone_id', '=', zone.id),
                ('state', '=', 'completed')
            ])
            zone.delivery_count = len(deliveries)
            if deliveries:
                zone.avg_delivery_time = sum(deliveries.mapped('total_delivery_time')) / len(deliveries)
            else:
                zone.avg_delivery_time = 0

