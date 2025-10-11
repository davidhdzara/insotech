# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Delivery Fields
    is_delivery = fields.Boolean(string='Is Delivery Order', default=False)
    delivery_order_id = fields.Many2one('pos.delivery.order', string='Delivery Order', 
                                         readonly=True, copy=False)
    delivery_order_count = fields.Integer(string='Delivery Orders', 
                                          compute='_compute_delivery_order_count')

    @api.depends('delivery_order_id')
    def _compute_delivery_order_count(self):
        """Count related delivery orders"""
        for order in self:
            order.delivery_order_count = 1 if order.delivery_order_id else 0

    def action_create_delivery_order(self):
        """Open wizard to create delivery order"""
        self.ensure_one()
        
        # Check if already has delivery order
        if self.delivery_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Delivery Order'),
                'res_model': 'pos.delivery.order',
                'res_id': self.delivery_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Create new delivery order directly
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Delivery Order'),
            'res_model': 'pos.delivery.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pos_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_delivery_phone': self.partner_id.phone or self.partner_id.mobile,
                'default_delivery_address': self._get_partner_address(),
            }
        }

    def action_view_delivery_order(self):
        """View related delivery order"""
        self.ensure_one()
        if not self.delivery_order_id:
            return self.action_create_delivery_order()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Order'),
            'res_model': 'pos.delivery.order',
            'res_id': self.delivery_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_partner_address(self):
        """Get formatted partner address"""
        self.ensure_one()
        partner = self.partner_id
        address_parts = []
        
        if partner.street:
            address_parts.append(partner.street)
        if partner.street2:
            address_parts.append(partner.street2)
        if partner.city:
            address_parts.append(partner.city)
        if partner.state_id:
            address_parts.append(partner.state_id.name)
        if partner.zip:
            address_parts.append(partner.zip)
            
        return ', '.join(address_parts) if address_parts else ''
    
    def write(self, vals):
        """Auto-create delivery when order is ready"""
        result = super(PosOrder, self).write(vals)
        
        # Check if this is a delivery-only POS and state changed to 'done' or 'paid'
        for order in self:
            if (order.config_id.is_delivery_only and 
                order.state in ['done', 'paid'] and 
                not order.delivery_order_id):
                
                # Skip if no customer is assigned
                if not order.partner_id:
                    order.message_post(
                        body=_("Cannot create delivery order: No customer assigned to this order")
                    )
                    continue
                
                # Create delivery order automatically
                delivery_vals = {
                    'pos_order_id': order.id,
                    'partner_id': order.partner_id.id,
                    'delivery_address': order._get_partner_address() or 'No address provided',
                    'delivery_phone': order.partner_id.phone or order.partner_id.mobile or '',
                    'state': 'pending',  # Start as pending, will be assigned later
                }
                
                # Create the delivery order
                delivery_order = self.env['pos.delivery.order'].create(delivery_vals)
                order.delivery_order_id = delivery_order.id
                
                # Notify
                order.message_post(
                    body=_("Delivery order %s created automatically") % delivery_order.name
                )
        
        return result

