# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_delivery_only = fields.Boolean(
        string='Solo Entregas',
        default=False,
        help="Active esta opción para puntos de venta que solo manejan órdenes de entrega."
    )

