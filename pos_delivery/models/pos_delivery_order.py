# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class PosDeliveryOrder(models.Model):
    _name = 'pos.delivery.order'
    _description = 'POS Delivery Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, priority desc'

    # Basic Information
    name = fields.Char(string='Delivery Number', required=True, copy=False, readonly=True, 
                       default=lambda self: _('New'), tracking=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Order', required=True, 
                                    ondelete='cascade', tracking=True)
    
    # Customer Information
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    delivery_address = fields.Text(string='Delivery Address', required=True, tracking=True)
    delivery_phone = fields.Char(string='Delivery Phone', tracking=True)
    delivery_latitude = fields.Float(string='Latitude', digits=(10, 7))
    delivery_longitude = fields.Float(string='Longitude', digits=(10, 7))
    
    # Delivery Information
    delivery_person_id = fields.Many2one('res.partner', string='Delivery Person', 
                                          domain=[('is_delivery_person', '=', True)],
                                          tracking=True)
    delivery_zone_id = fields.Many2one('delivery.zone', string='Delivery Zone', tracking=True)
    delivery_cost = fields.Monetary(string='Delivery Cost', currency_field='currency_id', tracking=True)
    
    # Status and Priority
    state = fields.Selection([
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='pending', required=True, tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)
    
    # Time Tracking
    create_date = fields.Datetime(string='Created Date', readonly=True)
    assigned_date = fields.Datetime(string='Assigned Date', readonly=True, tracking=True)
    in_transit_date = fields.Datetime(string='In Transit Date', readonly=True, tracking=True)
    completed_date = fields.Datetime(string='Completed Date', readonly=True, tracking=True)
    estimated_delivery_time = fields.Datetime(string='Estimated Delivery Time', tracking=True)
    
    # Computed Time Fields
    total_delivery_time = fields.Float(string='Total Time (minutes)', compute='_compute_delivery_time', 
                                        store=True, help="Time from creation to completion")
    time_elapsed = fields.Char(string='Time Elapsed', compute='_compute_time_elapsed')
    
    # Comments and Notes
    warehouse_notes = fields.Text(string='Warehouse Notes', help="Internal notes from warehouse staff")
    delivery_notes = fields.Text(string='Delivery Notes', help="Notes from delivery person")
    customer_notes = fields.Text(string='Customer Notes', help="Special instructions from customer")
    
    # Proof of Delivery
    delivery_photo = fields.Binary(string='Delivery Photo', attachment=True)
    delivery_photo_filename = fields.Char(string='Photo Filename')
    signature = fields.Binary(string='Customer Signature', attachment=True)
    
    # Rating
    rating = fields.Selection([
        ('1', '⭐'),
        ('2', '⭐⭐'),
        ('3', '⭐⭐⭐'),
        ('4', '⭐⭐⭐⭐'),
        ('5', '⭐⭐⭐⭐⭐')
    ], string='Customer Rating', tracking=True)
    rating_comment = fields.Text(string='Rating Comment')
    
    # Related Fields from POS Order
    order_total = fields.Monetary(related='pos_order_id.amount_total', string='Order Total', 
                                   currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one(related='pos_order_id.currency_id', readonly=True)
    
    # Color for Kanban
    color = fields.Integer(string='Color Index', compute='_compute_color', store=True)
    
    # Portal Access
    access_token = fields.Char('Security Token', copy=False)

    @api.model
    def create(self, vals):
        """Generate sequence number on creation"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.delivery.order') or _('New')
        if not vals.get('access_token'):
            vals['access_token'] = self._generate_access_token()
        
        # Auto-set delivery cost and estimated time from zone
        if vals.get('delivery_zone_id'):
            zone = self.env['delivery.zone'].browse(vals['delivery_zone_id'])
            if not vals.get('delivery_cost'):
                vals['delivery_cost'] = zone.delivery_cost
            if not vals.get('estimated_delivery_time') and zone.estimated_time:
                vals['estimated_delivery_time'] = fields.Datetime.now() + timedelta(minutes=zone.estimated_time)
        
        return super(PosDeliveryOrder, self).create(vals)

    @api.depends('state', 'priority')
    def _compute_color(self):
        """Set color based on priority and state"""
        for record in self:
            if record.state == 'completed':
                record.color = 10  # Green
            elif record.state == 'failed':
                record.color = 1   # Red
            elif record.priority == '3':
                record.color = 9   # Orange (urgent)
            elif record.priority == '2':
                record.color = 8   # Yellow (high)
            else:
                record.color = 0   # Default

    @api.depends('create_date', 'completed_date')
    def _compute_delivery_time(self):
        """Calculate total delivery time in minutes"""
        for record in self:
            if record.create_date and record.completed_date:
                delta = record.completed_date - record.create_date
                record.total_delivery_time = delta.total_seconds() / 60
            else:
                record.total_delivery_time = 0

    @api.depends('create_date', 'state')
    def _compute_time_elapsed(self):
        """Calculate time elapsed since creation"""
        for record in self:
            if record.create_date:
                if record.state in ['completed', 'failed']:
                    end_time = record.completed_date or fields.Datetime.now()
                else:
                    end_time = fields.Datetime.now()
                
                delta = end_time - record.create_date
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                
                if hours > 0:
                    record.time_elapsed = f"{hours}h {minutes}m"
                else:
                    record.time_elapsed = f"{minutes}m"
            else:
                record.time_elapsed = "0m"

    def write(self, vals):
        """Auto-update state when delivery person is assigned"""
        result = super(PosDeliveryOrder, self).write(vals)
        
        # Auto-assign when delivery person is set and state is pending
        if vals.get('delivery_person_id') and self.state == 'pending':
            super(PosDeliveryOrder, self).write({
                'state': 'assigned',
                'assigned_date': fields.Datetime.now()
            })
        
        # Auto-reset to pending if delivery person is removed and state is assigned
        if 'delivery_person_id' in vals and not vals['delivery_person_id'] and self.state == 'assigned':
            super(PosDeliveryOrder, self).write({
                'state': 'pending',
                'assigned_date': False
            })
        
        return result
    
    def action_assign(self):
        """Assign delivery to a delivery person"""
        self.ensure_one()
        if not self.delivery_person_id:
            raise UserError(_("Please select a delivery person before assigning."))
        self.write({
            'state': 'assigned',
            'assigned_date': fields.Datetime.now()
        })
        self._send_notification('assigned')

    def action_start_transit(self):
        """Mark delivery as in transit"""
        self.ensure_one()
        self.write({
            'state': 'in_transit',
            'in_transit_date': fields.Datetime.now()
        })
        self._send_notification('in_transit')

    def action_complete(self):
        """Mark delivery as completed"""
        self.ensure_one()
        
        # Check configuration requirements
        config = self.env['pos.delivery.config'].sudo().get_config()
        
        # Validate photo requirement
        if config.enable_photo_required and not self.delivery_photo:
            raise UserError(_("Delivery photo is required to complete this delivery. Please upload a photo."))
        
        # Validate signature requirement
        if config.enable_signature_required and not self.signature:
            raise UserError(_("Customer signature is required to complete this delivery."))
        
        self.write({
            'state': 'completed',
            'completed_date': fields.Datetime.now()
        })
        self._send_notification('completed')

    def action_fail(self):
        """Mark delivery as failed"""
        self.ensure_one()
        self.write({
            'state': 'failed',
            'completed_date': fields.Datetime.now()
        })
        self._send_notification('failed')

    def action_reset_to_pending(self):
        """Reset delivery to pending state"""
        self.ensure_one()
        self.write({
            'state': 'pending',
            'delivery_person_id': False,
            'assigned_date': False,
            'in_transit_date': False,
            'completed_date': False
        })

    def _send_notification(self, event_type):
        """Send notification on state change"""
        self.ensure_one()
        # Prepare notification message
        messages = {
            'assigned': _("Delivery %s has been assigned to %s") % (self.name, self.delivery_person_id.name),
            'in_transit': _("Delivery %s is now in transit") % self.name,
            'completed': _("Delivery %s has been completed") % self.name,
            'failed': _("Delivery %s has failed") % self.name,
        }
        
        # Post message in chatter
        self.message_post(body=messages.get(event_type, ''), message_type='notification')

    def _generate_access_token(self):
        """Generate secure token for portal access"""
        import secrets
        return secrets.token_urlsafe(32)

    def action_open_pos_order(self):
        """Open related POS order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('POS Order'),
            'res_model': 'pos.order',
            'res_id': self.pos_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

