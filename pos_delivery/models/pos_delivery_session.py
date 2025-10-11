# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class PosDeliverySession(models.Model):
    _name = 'pos.delivery.session'
    _description = 'Delivery Person App Session'
    _order = 'last_activity desc'

    delivery_person_id = fields.Many2one(
        'res.partner',
        string='Delivery Person',
        required=True,
        domain=[('is_delivery_person', '=', True)]
    )
    token = fields.Char(
        string='Access Token',
        required=True,
        index=True
    )
    device_info = fields.Text(
        string='Device Information',
        help='JSON string with device details'
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='If false, this session is no longer valid'
    )
    expires_at = fields.Datetime(
        string='Expires At',
        required=True,
        default=lambda self: datetime.now() + timedelta(days=30)
    )
    last_activity = fields.Datetime(
        string='Last Activity',
        default=fields.Datetime.now
    )
    create_date = fields.Datetime(
        string='Created',
        readonly=True
    )

    @api.model
    def cleanup_expired_sessions(self):
        """Cron job to cleanup expired sessions"""
        expired_sessions = self.search([
            '|',
            ('expires_at', '<', datetime.now()),
            ('is_active', '=', False)
        ])
        expired_sessions.unlink()

