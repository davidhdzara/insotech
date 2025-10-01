# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeliveryZone(models.Model):
    _name = 'delivery.zone'
    _description = 'Delivery Zone'
    _order = 'name'

    name = fields.Char(string='Zone Name', required=True)
    code = fields.Char(string='Zone Code', required=True)
    delivery_cost = fields.Monetary(string='Delivery Cost', currency_field='currency_id')
    estimated_time = fields.Integer(string='Estimated Time (minutes)', 
                                     help="Average delivery time for this zone")
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                   default=lambda self: self.env.company.currency_id)
    
    # Statistics
    delivery_count = fields.Integer(string='Total Deliveries', compute='_compute_statistics')
    avg_delivery_time = fields.Float(string='Avg. Delivery Time (min)', 
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

