# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Delivery Person Fields
    is_delivery_person = fields.Boolean(string='Is Delivery Person', default=False)
    delivery_person_code = fields.Char(string='Delivery Person Code')
    vehicle_type = fields.Selection([
        ('bike', 'Bike'),
        ('motorcycle', 'Motorcycle'),
        ('car', 'Car'),
        ('bicycle', 'Bicycle'),
        ('scooter', 'Scooter')
    ], string='Vehicle Type')
    vehicle_plate = fields.Char(string='Vehicle Plate')
    
    # Statistics
    total_deliveries = fields.Integer(string='Total Deliveries', compute='_compute_delivery_stats')
    completed_deliveries = fields.Integer(string='Completed Deliveries', 
                                          compute='_compute_delivery_stats')
    failed_deliveries = fields.Integer(string='Failed Deliveries', compute='_compute_delivery_stats')
    avg_rating = fields.Float(string='Average Rating', compute='_compute_delivery_stats', 
                               digits=(2, 1))
    avg_delivery_time = fields.Float(string='Avg. Delivery Time (min)', 
                                      compute='_compute_delivery_stats')

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
                
                # Calculate average rating
                rated_deliveries = deliveries.filtered(lambda d: d.rating)
                if rated_deliveries:
                    total_rating = sum(int(d.rating) for d in rated_deliveries)
                    partner.avg_rating = total_rating / len(rated_deliveries)
                else:
                    partner.avg_rating = 0
                
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
                partner.avg_rating = 0
                partner.avg_delivery_time = 0

    def action_view_deliveries(self):
        """View all deliveries for this person"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('My Deliveries'),
            'res_model': 'pos.delivery.order',
            'view_mode': 'list,kanban,form',
            'domain': [('delivery_person_id', '=', self.id)],
            'context': {'default_delivery_person_id': self.id}
        }

