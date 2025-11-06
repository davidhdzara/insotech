# -*- coding: utf-8 -*-

from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _get_receipt_render_env(self):
        """Override to inject customer data into receipt rendering"""
        result = super()._get_receipt_render_env()
        
        # Add customer information to the receipt context
        if self.partner_id:
            result['partner_info'] = {
                'name': self.partner_id.name or '',
                'street': self.partner_id.street or '',
                'street2': self.partner_id.street2 or '',
                'city': self.partner_id.city or '',
                'state': self.partner_id.state_id.name if self.partner_id.state_id else '',
                'zip': self.partner_id.zip or '',
                'country': self.partner_id.country_id.name if self.partner_id.country_id else '',
                'phone': self.partner_id.phone or '',
                'mobile': self.partner_id.mobile or '',
            }
        
        return result

