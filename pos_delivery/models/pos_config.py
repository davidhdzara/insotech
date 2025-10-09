# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_delivery_only = fields.Boolean(
        string='Delivery Only',
        default=False,
        help="Enable this for points of sale that only handle delivery orders."
    )

