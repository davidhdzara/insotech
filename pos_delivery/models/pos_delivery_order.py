# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class PosDeliveryOrder(models.Model):
    _name = 'pos.delivery.order'
    _description = 'Orden de Entrega POS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'state_sequence, priority desc, create_date desc'

    # Basic Information
    name = fields.Char(string='Número de Entrega', required=True, copy=False, readonly=True, 
                       default=lambda self: _('Nuevo'), tracking=True)
    display_name_with_ticket = fields.Char(string='Número de Orden', compute='_compute_display_name_with_ticket', 
                                            store=False)
    pos_order_id = fields.Many2one('pos.order', string='Orden POS', required=False, 
                                    ondelete='cascade', tracking=True,
                                    help="Orden POS relacionada (opcional)")
    
    @api.depends('pos_order_id', 'pos_order_id.tracking_number', 'pos_order_id.pos_reference', 'name')
    def _compute_display_name_with_ticket(self):
        """Display ticket number if POS order exists, otherwise delivery name"""
        for record in self:
            if record.pos_order_id:
                # Use tracking_number which is the "Order Number" field (e.g. "610")
                if hasattr(record.pos_order_id, 'tracking_number') and record.pos_order_id.tracking_number:
                    record.display_name_with_ticket = str(record.pos_order_id.tracking_number)
                elif record.pos_order_id.pos_reference:
                    record.display_name_with_ticket = record.pos_order_id.pos_reference
                else:
                    record.display_name_with_ticket = record.pos_order_id.name
            else:
                record.display_name_with_ticket = record.name or 'Nuevo'
    
    # Customer Information
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    delivery_address = fields.Text(string='Dirección de Entrega', required=True, tracking=True)
    delivery_phone = fields.Char(string='Teléfono de Entrega', tracking=True)
    delivery_latitude = fields.Float(string='Latitud', digits=(10, 7))
    delivery_longitude = fields.Float(string='Longitud', digits=(10, 7))
    
    # Delivery Information
    delivery_person_id = fields.Many2one('res.partner', string='Repartidor', 
                                          domain=[('is_delivery_person', '=', True)],
                                          tracking=True)
    delivery_zone_id = fields.Many2one('delivery.zone', string='Zona de Entrega', tracking=True)
    delivery_cost = fields.Monetary(string='Costo de Envío', currency_field='currency_id', tracking=True)
    delivery_payment_method = fields.Selection([
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia')
    ], string='Método de Pago Envío', tracking=True, help="Método de pago del costo de envío")
    
    # Status and Priority
    # Order in Selection defines kanban column order
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('assigned', 'Asignado'),
        ('in_transit', 'En Tránsito'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], string='Estado', default='pending', required=True, tracking=True)
    
    state_sequence = fields.Integer(string='Secuencia de Estado', compute='_compute_state_sequence', store=True)
    
    priority = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Normal'),
        ('2', 'Alta'),
        ('3', 'Urgente')
    ], string='Prioridad', default='1', tracking=True)
    
    # Time Tracking
    create_date = fields.Datetime(string='Fecha de Creación', readonly=True)
    assigned_date = fields.Datetime(string='Fecha de Asignación', readonly=True, tracking=True)
    in_transit_date = fields.Datetime(string='Fecha en Tránsito', readonly=True, tracking=True)
    completed_date = fields.Datetime(string='Fecha de Completado', readonly=True, tracking=True)
    estimated_delivery_time = fields.Datetime(string='Tiempo Estimado de Entrega', tracking=True)
    
    # Computed Time Fields
    total_delivery_time = fields.Float(string='Tiempo Total (minutos)', compute='_compute_delivery_time', 
                                        store=True, help="Tiempo desde la creación hasta la finalización")
    time_elapsed = fields.Char(string='Tiempo Transcurrido', compute='_compute_time_elapsed')
    
    # Stage Time Tracking
    stage_time_ids = fields.One2many('pos.delivery.stage.time', 'delivery_order_id', 
                                     string='Stage Times', readonly=True)
    stage_time_count = fields.Integer(string='Stage Changes', compute='_compute_stage_time_count')
    
    # Individual Stage Durations (computed from stage_time_ids)
    time_in_pending = fields.Float(string='Time in Pending (min)', compute='_compute_stage_durations', 
                                   store=True, help="Time spent in Pending state")
    time_in_assigned = fields.Float(string='Time in Assigned (min)', compute='_compute_stage_durations', 
                                    store=True, help="Time spent in Assigned state")
    time_in_transit = fields.Float(string='Time in Transit (min)', compute='_compute_stage_durations', 
                                   store=True, help="Time spent in In Transit state")
    time_in_completed = fields.Float(string='Time in Completed (min)', compute='_compute_stage_durations', 
                                     store=True, help="Time in final state")
    time_in_failed = fields.Float(string='Time in Failed (min)', compute='_compute_stage_durations', 
                                  store=True, help="Time in failed state")
    
    # Display fields for stage times
    time_pending_display = fields.Char(string='Pending Duration', compute='_compute_stage_durations_display')
    time_assigned_display = fields.Char(string='Assigned Duration', compute='_compute_stage_durations_display')
    time_transit_display = fields.Char(string='Transit Duration', compute='_compute_stage_durations_display')
    time_completed_display = fields.Char(string='Completed Duration', compute='_compute_stage_durations_display')
    
    # Comments and Notes
    warehouse_notes = fields.Text(string='Notas del Almacén', help="Notas internas del personal del almacén")
    delivery_notes = fields.Text(string='Notas del Repartidor', help="Notas del repartidor")
    customer_notes = fields.Text(string='Notas del Cliente', help="Instrucciones especiales del cliente")
    pos_general_note = fields.Text(string='Nota General POS', compute='_compute_pos_general_note', 
                                    help="Nota general de la orden POS")
    
    # Proof of Delivery
    delivery_photo = fields.Binary(string='Foto de Entrega', attachment=True)
    delivery_photo_filename = fields.Char(string='Nombre del Archivo de Foto')
    signature = fields.Binary(string='Firma del Cliente', attachment=True)
    
    # Related Fields from POS Order or Manual Entry
    order_total = fields.Monetary(string='Total de Orden', currency_field='currency_id', 
                                   compute='_compute_order_total', store=True, readonly=False,
                                   help="Total de la orden (desde POS o manual)")
    order_total_manual = fields.Monetary(string='Total Manual', currency_field='currency_id',
                                         help="Total manual cuando no hay orden POS")
    payment_method_name = fields.Char(string='Método de Pago', compute='_compute_payment_method_name', 
                                       store=True, readonly=True,
                                       help="Método de pago de la orden POS")
    currency_id = fields.Many2one('res.currency', string='Moneda', 
                                   compute='_compute_currency', store=True, readonly=False,
                                   default=lambda self: self.env.company.currency_id)
    
    # Color for Kanban
    color = fields.Integer(string='Índice de Color', compute='_compute_color', store=True)
    
    # Portal Access
    access_token = fields.Char('Token de Seguridad', copy=False)

    # Invoice Status
    has_invoice = fields.Boolean(string='Tiene Factura', compute='_compute_has_invoice', 
                                  help="Indica si la orden POS ya tiene una factura generada")

    @api.depends('pos_order_id', 'pos_order_id.account_move')
    def _compute_has_invoice(self):
        """Check if the associated POS order has an invoice"""
        for record in self:
            record.has_invoice = bool(record.pos_order_id and record.pos_order_id.account_move)
    
    @api.depends('pos_order_id', 'pos_order_id.general_note')
    def _compute_pos_general_note(self):
        """Get general note from POS order"""
        for record in self:
            record.pos_general_note = record.pos_order_id.general_note if record.pos_order_id else ''
    
    @api.depends('pos_order_id', 'pos_order_id.payment_ids', 'pos_order_id.payment_ids.payment_method_id')
    def _compute_payment_method_name(self):
        """Get the payment method name from the POS order"""
        for record in self:
            if record.pos_order_id and record.pos_order_id.payment_ids:
                # Get the first payment method (as per user note: orders only have one payment method)
                record.payment_method_name = record.pos_order_id.payment_ids[0].payment_method_id.name
            else:
                record.payment_method_name = False

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number on creation"""
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pos.delivery.order') or _('Nuevo')
            if not vals.get('access_token'):
                vals['access_token'] = self._generate_access_token()
            
            # Auto-set delivery cost and estimated time from zone
            if vals.get('delivery_zone_id'):
                zone = self.env['delivery.zone'].browse(vals['delivery_zone_id'])
                if not vals.get('delivery_cost'):
                    vals['delivery_cost'] = zone.delivery_cost
                if not vals.get('estimated_delivery_time') and zone.estimated_time:
                    vals['estimated_delivery_time'] = fields.Datetime.now() + timedelta(minutes=zone.estimated_time)
        
        records = super(PosDeliveryOrder, self).create(vals_list)
        
        # Start tracking time in initial state for each record
        for record, vals in zip(records, vals_list):
            record._start_stage_timer(vals.get('state', 'pending'))
        
        return records

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
    
    @api.depends('state')
    def _compute_state_sequence(self):
        """Compute sequence number for state ordering in kanban"""
        state_order = {
            'pending': 1,
            'assigned': 2,
            'in_transit': 3,
            'completed': 4,
            'failed': 5,
        }
        for record in self:
            record.state_sequence = state_order.get(record.state, 999)
    
    @api.depends('pos_order_id', 'pos_order_id.amount_total', 'order_total_manual')
    def _compute_order_total(self):
        """Compute order total from POS order or manual entry"""
        for record in self:
            if record.pos_order_id:
                record.order_total = record.pos_order_id.amount_total
            else:
                record.order_total = record.order_total_manual or 0.0
    
    @api.depends('pos_order_id', 'pos_order_id.currency_id')
    def _compute_currency(self):
        """Compute currency from POS order or company"""
        for record in self:
            if record.pos_order_id and record.pos_order_id.currency_id:
                record.currency_id = record.pos_order_id.currency_id
            elif not record.currency_id:
                record.currency_id = self.env.company.currency_id

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
    
    @api.depends('stage_time_ids')
    def _compute_stage_time_count(self):
        """Count stage time entries"""
        for record in self:
            record.stage_time_count = len(record.stage_time_ids)
    
    @api.depends('stage_time_ids.duration', 'stage_time_ids.stage', 'stage_time_ids.is_active')
    def _compute_stage_durations(self):
        """Calculate total time spent in each stage"""
        for record in self:
            # Initialize all times to 0
            record.time_in_pending = 0
            record.time_in_assigned = 0
            record.time_in_transit = 0
            record.time_in_completed = 0
            record.time_in_failed = 0
            
            # Sum up times for each stage
            for stage_time in record.stage_time_ids:
                if stage_time.stage == 'pending':
                    record.time_in_pending += stage_time.duration
                elif stage_time.stage == 'assigned':
                    record.time_in_assigned += stage_time.duration
                elif stage_time.stage == 'in_transit':
                    record.time_in_transit += stage_time.duration
                elif stage_time.stage == 'completed':
                    record.time_in_completed += stage_time.duration
                elif stage_time.stage == 'failed':
                    record.time_in_failed += stage_time.duration
    
    @api.depends('time_in_pending', 'time_in_assigned', 'time_in_transit', 'time_in_completed')
    def _compute_stage_durations_display(self):
        """Format stage durations for display"""
        for record in self:
            record.time_pending_display = record._format_duration(record.time_in_pending)
            record.time_assigned_display = record._format_duration(record.time_in_assigned)
            record.time_transit_display = record._format_duration(record.time_in_transit)
            record.time_completed_display = record._format_duration(record.time_in_completed)
    
    def _format_duration(self, minutes):
        """Format duration in minutes to human readable format"""
        if minutes >= 1440:  # More than 24 hours
            days = int(minutes // 1440)
            hours = int((minutes % 1440) // 60)
            mins = int(minutes % 60)
            return f"{days}d {hours}h {mins}m"
        elif minutes >= 60:  # More than 1 hour
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}m"
        else:
            return f"{int(minutes)}m"

    def write(self, vals):
        """Auto-update state when delivery person is assigned and track stage changes"""
        # Track state changes for stage timing
        result = super(PosDeliveryOrder, self).write(vals)
        
        for record in self:
            old_state = record.state
            
            # If state changed, update stage timers
            if 'state' in vals and vals['state'] != old_state:
                record._end_stage_timer(old_state)
                record._start_stage_timer(vals['state'])
            
            # Auto-assign when delivery person is set and state is pending
            if vals.get('delivery_person_id') and record.state == 'pending':
                super(PosDeliveryOrder, record).write({
                    'state': 'assigned',
                    'assigned_date': fields.Datetime.now()
                })
                record._end_stage_timer('pending')
                record._start_stage_timer('assigned')
            
            # Auto-reset to pending if delivery person is removed and state is assigned
            if 'delivery_person_id' in vals and not vals['delivery_person_id'] and record.state == 'assigned':
                super(PosDeliveryOrder, record).write({
                    'state': 'pending',
                    'assigned_date': False
                })
                record._end_stage_timer('assigned')
                record._start_stage_timer('pending')
        
        return result
    
    def action_assign(self):
        """Assign delivery to a delivery person"""
        self.ensure_one()
        if not self.delivery_person_id:
            raise UserError(_("Por favor seleccione un repartidor antes de asignar."))
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
            raise UserError(_("Se requiere una foto de entrega para completar esta entrega. Por favor suba una foto."))
        
        # Validate signature requirement
        if config.enable_signature_required and not self.signature:
            raise UserError(_("Se requiere la firma del cliente para completar esta entrega."))
        
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
            'assigned': _("La entrega %s ha sido asignada a %s") % (self.name, self.delivery_person_id.name),
            'in_transit': _("La entrega %s está ahora en tránsito") % self.name,
            'completed': _("La entrega %s ha sido completada") % self.name,
            'failed': _("La entrega %s ha fallado") % self.name,
        }
        
        # Post message in chatter
        self.message_post(body=messages.get(event_type, ''), message_type='notification')

    def _generate_access_token(self):
        """Generate secure token for portal access"""
        import secrets
        return secrets.token_urlsafe(32)
    
    # ==================== Receipt Management ====================
    
    def action_view_receipt(self):
        """View the POS receipt for this delivery order"""
        self.ensure_one()
        
        # Return action to display the receipt in a new window
        # Now using delivery order ID instead of POS order ID
        return {
            'name': _('Tirilla de la Orden'),
            'type': 'ir.actions.act_url',
            'url': '/pos/delivery/receipt/html/' + str(self.id),
            'target': 'new',
        }
    
    def action_view_pos_order(self):
        """View the associated POS order"""
        self.ensure_one()
        
        if not self.pos_order_id:
            raise UserError(_('Esta orden de domicilio no tiene una orden POS asociada.'))
        
        return {
            'name': _('Orden POS'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'res_id': self.pos_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _start_stage_timer(self, stage):
        """Start timing a new stage"""
        self.ensure_one()
        self.env['pos.delivery.stage.time'].sudo().create({
            'delivery_order_id': self.id,
            'stage': stage,
            'start_time': fields.Datetime.now(),
            'is_active': True,
        })
    
    def _end_stage_timer(self, stage):
        """End timing for a stage"""
        self.ensure_one()
        # Find active stage time record for this stage
        active_stage = self.env['pos.delivery.stage.time'].search([
            ('delivery_order_id', '=', self.id),
            ('stage', '=', stage),
            ('is_active', '=', True)
        ], limit=1)
        
        if active_stage:
            active_stage.sudo().write({
                'end_time': fields.Datetime.now(),
                'is_active': False,
            })
    
    def action_view_stage_times(self):
        """Open stage times view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stage Time Details'),
            'res_model': 'pos.delivery.stage.time',
            'view_mode': 'list,form',
            'domain': [('delivery_order_id', '=', self.id)],
            'context': {'default_delivery_order_id': self.id},
            'target': 'current',
        }

    def action_open_pos_order(self):
        """Open related POS order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden POS'),
            'res_model': 'pos.order',
            'res_id': self.pos_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

