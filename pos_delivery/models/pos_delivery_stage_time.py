# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class PosDeliveryStageTime(models.Model):
    """Track time spent in each state/stage"""
    _name = 'pos.delivery.stage.time'
    _description = 'Delivery Order Stage Time Tracking'
    _order = 'start_time desc'

    delivery_order_id = fields.Many2one('pos.delivery.order', string='Delivery Order', 
                                        required=True, ondelete='cascade', index=True)
    stage = fields.Selection([
        ('pending', 'Pendiente'),
        ('assigned', 'Asignado'),
        ('in_transit', 'En Tránsito'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], string='Stage', required=True, index=True)
    
    start_time = fields.Datetime(string='Start Time', required=True, 
                                  default=fields.Datetime.now, index=True)
    end_time = fields.Datetime(string='End Time')
    
    duration = fields.Float(string='Duration (minutes)', compute='_compute_duration', 
                           store=True, help="Time spent in this stage in minutes")
    duration_hours = fields.Float(string='Duration (hours)', compute='_compute_duration_hours', 
                                  store=True, help="Time spent in this stage in hours")
    duration_display = fields.Char(string='Duration', compute='_compute_duration_display',
                                   help="Human readable duration")
    
    is_active = fields.Boolean(string='Active', default=True, 
                               help="True if currently in this stage")
    
    @api.depends('start_time', 'end_time', 'is_active')
    def _compute_duration(self):
        """Calculate duration in minutes"""
        for record in self:
            if record.start_time:
                end = record.end_time if record.end_time else fields.Datetime.now()
                delta = end - record.start_time
                record.duration = delta.total_seconds() / 60
            else:
                record.duration = 0
    
    @api.depends('duration')
    def _compute_duration_hours(self):
        """Calculate duration in hours"""
        for record in self:
            record.duration_hours = record.duration / 60
    
    @api.depends('duration')
    def _compute_duration_display(self):
        """Format duration for display"""
        for record in self:
            if record.duration >= 1440:  # More than 24 hours
                days = int(record.duration // 1440)
                hours = int((record.duration % 1440) // 60)
                minutes = int(record.duration % 60)
                record.duration_display = f"{days}d {hours}h {minutes}m"
            elif record.duration >= 60:  # More than 1 hour
                hours = int(record.duration // 60)
                minutes = int(record.duration % 60)
                record.duration_display = f"{hours}h {minutes}m"
            else:
                minutes = int(record.duration)
                record.duration_display = f"{minutes}m"
    
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            stage_name = dict(record._fields['stage'].selection).get(record.stage)
            name = f"{record.delivery_order_id.name} - {stage_name} ({record.duration_display})"
            result.append((record.id, name))
        return result

