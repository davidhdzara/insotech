# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DeliveryHistory(models.Model):
    _name = 'delivery.history'
    _description = 'Delivery History Log'
    _order = 'create_date desc'

    delivery_order_id = fields.Many2one('pos.delivery.order', string='Delivery Order', 
                                         required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Person', 
                                  help="Delivery person or staff member who made the change")
    
    # Event Information
    event_type = fields.Selection([
        ('created', 'Created'),
        ('assigned', 'Assigned'),
        ('started', 'Started Delivery'),
        ('location_updated', 'Location Updated'),
        ('photo_uploaded', 'Photo Uploaded'),
        ('comment_added', 'Comment Added'),
        ('priority_changed', 'Priority Changed'),
        ('zone_changed', 'Zone Changed'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('reassigned', 'Reassigned'),
    ], string='Event Type', required=True)
    
    old_state = fields.Char(string='Previous State')
    new_state = fields.Char(string='New State')
    description = fields.Text(string='Description')
    
    # Location Tracking
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    
    # Timestamps
    create_date = fields.Datetime(string='Date', readonly=True, default=fields.Datetime.now)
    
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"{record.delivery_order_id.name} - {dict(record._fields['event_type'].selection).get(record.event_type)}"
            result.append((record.id, name))
        return result


class PosDeliveryOrderHistory(models.Model):
    """Add history tracking to delivery orders"""
    _inherit = 'pos.delivery.order'

    history_ids = fields.One2many('delivery.history', 'delivery_order_id', 
                                   string='History', readonly=True)
    history_count = fields.Integer(string='History Count', compute='_compute_history_count')

    @api.depends('history_ids')
    def _compute_history_count(self):
        """Count history entries"""
        for record in self:
            record.history_count = len(record.history_ids)

    def _log_history(self, event_type, description=None, old_state=None, new_state=None):
        """Log an event in history"""
        self.ensure_one()
        
        vals = {
            'delivery_order_id': self.id,
            'event_type': event_type,
            'description': description,
            'old_state': old_state,
            'new_state': new_state,
            'partner_id': self.delivery_person_id.id if self.delivery_person_id else False,
        }
        
        # Add current location if available
        if self.delivery_latitude and self.delivery_longitude:
            vals['latitude'] = self.delivery_latitude
            vals['longitude'] = self.delivery_longitude
        
        self.env['delivery.history'].sudo().create(vals)

    @api.model
    def create(self, vals):
        """Log creation in history"""
        record = super(PosDeliveryOrderHistory, self).create(vals)
        record._log_history('created', description=_('Delivery order created'))
        return record

    def write(self, vals):
        """Log important changes in history"""
        for record in self:
            old_state = record.state
            old_priority = record.priority
            old_zone = record.delivery_zone_id.name if record.delivery_zone_id else None
            old_person = record.delivery_person_id.name if record.delivery_person_id else None
            
            result = super(PosDeliveryOrderHistory, record).write(vals)
            
            # Log state changes
            if 'state' in vals and vals['state'] != old_state:
                event_map = {
                    'assigned': 'assigned',
                    'in_transit': 'started',
                    'completed': 'completed',
                    'failed': 'failed',
                }
                event_type = event_map.get(vals['state'], 'created')
                record._log_history(event_type, 
                                   description=_('Status changed from %s to %s') % (old_state, vals['state']),
                                   old_state=old_state,
                                   new_state=vals['state'])
            
            # Log priority changes
            if 'priority' in vals and vals['priority'] != old_priority:
                record._log_history('priority_changed',
                                   description=_('Priority changed from %s to %s') % (old_priority, vals['priority']))
            
            # Log zone changes
            if 'delivery_zone_id' in vals:
                new_zone = self.env['delivery.zone'].browse(vals['delivery_zone_id']).name if vals['delivery_zone_id'] else None
                if new_zone != old_zone:
                    record._log_history('zone_changed',
                                       description=_('Zone changed from %s to %s') % (old_zone or 'None', new_zone or 'None'))
            
            # Log delivery person changes
            if 'delivery_person_id' in vals:
                new_person = self.env['res.partner'].browse(vals['delivery_person_id']).name if vals['delivery_person_id'] else None
                if new_person != old_person:
                    record._log_history('reassigned',
                                       description=_('Delivery person changed from %s to %s') % (old_person or 'None', new_person or 'None'))
            
            # Log photo upload
            if 'delivery_photo' in vals and vals['delivery_photo']:
                record._log_history('photo_uploaded',
                                   description=_('Delivery photo uploaded'))
            
            # Log location updates
            if 'delivery_latitude' in vals or 'delivery_longitude' in vals:
                record._log_history('location_updated',
                                   description=_('Location updated'))
            
            # Log comments
            if 'delivery_notes' in vals and vals['delivery_notes']:
                record._log_history('comment_added',
                                   description=_('Delivery notes added'))
            if 'warehouse_notes' in vals and vals['warehouse_notes']:
                record._log_history('comment_added',
                                   description=_('Warehouse notes added'))
            
            return result
        
        return super(PosDeliveryOrderHistory, self).write(vals)

    def action_view_history(self):
        """Open history view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery History'),
            'res_model': 'delivery.history',
            'view_mode': 'list,form',
            'domain': [('delivery_order_id', '=', self.id)],
            'context': {'default_delivery_order_id': self.id}
        }

