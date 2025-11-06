# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Delivery Fields
    is_delivery = fields.Boolean(string='Es Orden de Entrega', default=False)
    delivery_order_id = fields.Many2one('pos.delivery.order', string='Orden de Entrega', 
                                         readonly=True, copy=False)
    delivery_order_count = fields.Integer(string='Órdenes de Entrega', 
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
                'name': _('Orden de Entrega'),
                'res_model': 'pos.delivery.order',
                'res_id': self.delivery_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Create new delivery order directly
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear Orden de Entrega'),
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
            'name': _('Orden de Entrega'),
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
                        body=_("No se puede crear orden de entrega: No hay cliente asignado a esta orden")
                    )
                    continue
                
                # Create delivery order automatically
                delivery_vals = {
                    'pos_order_id': order.id,
                    'partner_id': order.partner_id.id,
                    'delivery_address': order._get_partner_address() or 'No se proporcionó dirección',
                    'delivery_phone': order.partner_id.phone or order.partner_id.mobile or '',
                    'state': 'pending',  # Start as pending, will be assigned later
                }
                
                # Create the delivery order
                delivery_order = self.env['pos.delivery.order'].create(delivery_vals)
                order.delivery_order_id = delivery_order.id
                
                # Send order to kitchen/printer if pos_restaurant module is installed
                try:
                    # Check if the order has lines that need to be sent to kitchen
                    if order.lines:
                        # Mark all lines as to be printed in kitchen
                        order.lines.write({'printer_state': 'pending'})
                        
                        # If pos_restaurant is installed, send to kitchen
                        if hasattr(order, '_send_orders'):
                            order._send_orders()
                except Exception as e:
                    # Log error but don't fail the delivery creation
                    order.message_post(
                        body=_("Advertencia: No se pudo enviar a cocina automáticamente. Error: %s") % str(e)
                    )
                
                # Notify
                order.message_post(
                    body=_("Orden de entrega %s creada automáticamente") % delivery_order.name
                )
        
        return result

