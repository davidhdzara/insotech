# -*- coding: utf-8 -*-

from odoo import models, fields

class TestRecord(models.Model):
    _name = 'test.record'
    _description = 'Test Record'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')