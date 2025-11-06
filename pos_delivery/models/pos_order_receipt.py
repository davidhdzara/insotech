# -*- coding: utf-8 -*-

from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _export_for_ui(self, order):
        """Override to add customer information to the receipt"""
        result = super()._export_for_ui(order)
        
        # Add customer details to receipt if customer exists
        if order.partner_id:
            result['partner'] = {
                'name': order.partner_id.name or '',
                'street': order.partner_id.street or '',
                'street2': order.partner_id.street2 or '',
                'city': order.partner_id.city or '',
                'state_id': order.partner_id.state_id.name if order.partner_id.state_id else '',
                'zip': order.partner_id.zip or '',
                'country_id': order.partner_id.country_id.name if order.partner_id.country_id else '',
                'phone': order.partner_id.phone or '',
                'mobile': order.partner_id.mobile or '',
            }
        
        return result

