# -*- coding: utf-8 -*-

from odoo import models, fields


class DeliveryAppQRWizard(models.TransientModel):
    _name = 'delivery.app.qr.wizard'
    _description = 'Wizard to display QR code for app configuration'

    qr_image = fields.Binary(
        string='QR Code',
        readonly=True,
        help='QR code image for app configuration'
    )
    config_json = fields.Text(
        string='Configuration',
        readonly=True,
        help='JSON configuration data'
    )
    server_url = fields.Char(
        string='Server URL',
        readonly=True
    )

