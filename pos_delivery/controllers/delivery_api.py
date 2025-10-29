# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request, Response
from datetime import datetime, timedelta
import secrets

_logger = logging.getLogger(__name__)


class DeliveryAPI(http.Controller):
    """REST API for Delivery App"""

    def _validate_token(self, token):
        """Validate delivery person token"""
        if not token:
            return None
        
        # Find active session for this token
        session = request.env['pos.delivery.session'].sudo().search([
            ('token', '=', token),
            ('is_active', '=', True),
            ('expires_at', '>', datetime.now())
        ], limit=1)
        
        if session:
            # Update last activity
            session.sudo().write({'last_activity': datetime.now()})
            return session.delivery_person_id
        
        return None

    def _json_response(self, data=None, error=None, status=200):
        """Standard JSON response - returns dict for Odoo's type='json' routes"""
        response_data = {
            'success': error is None,
            'timestamp': datetime.now().isoformat()
        }
        
        if data is not None:
            response_data['data'] = data
        
        if error:
            response_data['error'] = error
        
        # For type='json' routes, return dict directly (Odoo handles JSON conversion)
        return response_data

    @http.route('/api/delivery/config', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_config(self):
        """Get server configuration info"""
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'server_url': base_url,
                'api_version': '1.0',
                'websocket_url': base_url.replace('http://', 'ws://').replace('https://', 'wss://') + '/websocket'
            }
        }
        
        return Response(
            json.dumps(data, default=str),
            content_type='application/json',
            status=200
        )

    @http.route('/api/delivery/login', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def login(self, **kwargs):
        """
        Login for delivery person (portal user)
        Expected params: email, password, device_info
        """
        try:
            email = kwargs.get('email')
            password = kwargs.get('password')
            device_info = kwargs.get('device_info', {})
            
            if not email or not password:
                return self._json_response(error='Email y contraseña son requeridos', status=400)
            
            # Authenticate user directly checking credentials
            try:
                # Search for user by email
                user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                
                if not user:
                    _logger.error(f"User not found: {email}")
                    return self._json_response(error='Credenciales inválidas', status=401)
                
                # Check password using passlib (what Odoo uses internally)
                try:
                    from passlib.context import CryptContext
                    # Get the password hash from database
                    request.env.cr.execute(
                        "SELECT password FROM res_users WHERE id = %s", 
                        (user.id,)
                    )
                    result = request.env.cr.fetchone()
                    if not result or not result[0]:
                        _logger.error(f"No password hash found for {email}")
                        return self._json_response(error='Credenciales inválidas', status=401)
                    
                    stored_hash = result[0]
                    
                    # Verify password using CryptContext (same as Odoo)
                    crypt_context = CryptContext(schemes=['pbkdf2_sha512', 'plaintext'], deprecated=['plaintext'])
                    valid = crypt_context.verify(password, stored_hash)
                    
                    if not valid:
                        _logger.error(f"Password mismatch for {email}")
                        return self._json_response(error='Credenciales inválidas', status=401)
                    
                    uid = user.id
                except Exception as e:
                    _logger.error(f"Password check failed for {email}: {str(e)}")
                    return self._json_response(error='Credenciales inválidas', status=401)
                
            except Exception as e:
                _logger.error(f"Authentication error: {str(e)}")
                return self._json_response(error='Credenciales inválidas', status=401)
            
            # Get partner
            partner = user.partner_id
            
            if not partner.is_delivery_person:
                return self._json_response(
                    error='Este usuario no está configurado como domiciliario',
                    status=403
                )
            
            # Check if user is active (check on user, not partner)
            if not user.active:
                return self._json_response(
                    error='Tu cuenta está inactiva. Contacta al administrador.',
                    status=403
                )
            
            # Create session token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)
            
            # Create or update session
            session = request.env['pos.delivery.session'].sudo().create({
                'delivery_person_id': partner.id,
                'token': token,
                'device_info': json.dumps(device_info),
                'is_active': True,
                'expires_at': expires_at,
                'last_activity': datetime.now()
            })
            
            return self._json_response({
                'token': token,
                'expires_at': expires_at.isoformat(),
                'delivery_person': {
                    'id': partner.id,
                    'name': partner.name,
                    'email': partner.email,
                    'phone': partner.phone or partner.mobile,
                    'image': partner.image_128.decode('utf-8') if partner.image_128 else None,
                    'vehicle_type': partner.vehicle_type,
                    'delivery_count': partner.total_deliveries,
                    'rating': partner.avg_rating
                }
            })
            
        except Exception as e:
            _logger.error(f"Login error: {str(e)}")
            return self._json_response(error=f'Error en el servidor: {str(e)}', status=500)

    @http.route('/api/delivery/logout', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def logout(self, **kwargs):
        """Logout delivery person"""
        try:
            token = kwargs.get('token')
            
            if not token:
                return self._json_response(error='Token requerido', status=400)
            
            # Deactivate session
            session = request.env['pos.delivery.session'].sudo().search([
                ('token', '=', token)
            ])
            
            if session:
                session.sudo().write({'is_active': False})
            
            return self._json_response({'message': 'Sesión cerrada exitosamente'})
            
        except Exception as e:
            _logger.error(f"Logout error: {str(e)}")
            return self._json_response(error=str(e), status=500)

    @http.route('/api/delivery/orders', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_orders(self, **kwargs):
        """Get orders assigned to delivery person"""
        try:
            token = kwargs.get('token')
            status_filter = kwargs.get('status')  # pending, in_transit, completed
            
            delivery_person = self._validate_token(token)
            if not delivery_person:
                return self._json_response(error='Token inválido o expirado', status=401)
            
            # Build domain
            domain = [('delivery_person_id', '=', delivery_person.id)]
            
            if status_filter:
                domain.append(('state', '=', status_filter))
            else:
                # By default, show only active orders
                domain.append(('state', 'in', ['pending', 'assigned', 'in_transit']))
            
            # Get orders
            orders = request.env['pos.delivery.order'].sudo().search(
                domain,
                order='priority desc, create_date desc'
            )
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'name': order.name,
                    'pos_order_name': order.pos_order_id.name if order.pos_order_id else '',
                    'customer_name': order.partner_id.name if order.partner_id else 'Cliente',
                    'customer_phone': order.delivery_phone,
                    'delivery_address': order.delivery_address,
                    'state': order.state,
                    'state_label': dict(order._fields['state'].selection).get(order.state),
                    'priority': order.priority,
                     'priority_label': dict(order._fields['priority'].selection).get(order.priority),
                     'estimated_delivery': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                     'delivery_instructions': order.customer_notes or '',
                     'warehouse_comment': order.warehouse_notes or '',
                     'delivery_person_comment': order.delivery_notes or '',
                     'amount_total': float(order.pos_order_id.amount_total) if order.pos_order_id else 0,
                     'create_date': order.create_date.isoformat(),
                     'assigned_at': order.assigned_date.isoformat() if order.assigned_date else None,
                     'in_transit_at': order.in_transit_date.isoformat() if order.in_transit_date else None
                })
            
            return self._json_response({
                'orders': orders_data,
                'count': len(orders_data)
            })
            
        except Exception as e:
            _logger.error(f"Get orders error: {str(e)}")
            return self._json_response(error=str(e), status=500)

    @http.route('/api/delivery/orders/<int:order_id>', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_order_detail(self, order_id, **kwargs):
        """Get order detail"""
        try:
            token = kwargs.get('token')
            
            delivery_person = self._validate_token(token)
            if not delivery_person:
                return self._json_response(error='Token inválido o expirado', status=401)
            
            order = request.env['pos.delivery.order'].sudo().browse(order_id)
            
            if not order.exists():
                return self._json_response(error='Pedido no encontrado', status=404)
            
            if order.delivery_person_id.id != delivery_person.id:
                return self._json_response(error='No tienes permiso para ver este pedido', status=403)
            
            # Get order lines
            order_lines = []
            if order.pos_order_id:
                for line in order.pos_order_id.lines:
                    order_lines.append({
                        'product_name': line.product_id.name,
                        'quantity': line.qty,
                        'price_unit': float(line.price_unit),
                        'price_subtotal': float(line.price_subtotal)
                    })
            
            order_data = {
                'id': order.id,
                'name': order.name,
                'pos_order_name': order.pos_order_id.name if order.pos_order_id else '',
                'customer_name': order.partner_id.name if order.partner_id else 'Cliente',
                'customer_phone': order.delivery_phone,
                'delivery_address': order.delivery_address,
                'state': order.state,
                'state_label': dict(order._fields['state'].selection).get(order.state),
                'priority': order.priority,
                 'priority_label': dict(order._fields['priority'].selection).get(order.priority),
                 'estimated_delivery': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                 'delivery_instructions': order.customer_notes or '',
                 'warehouse_comment': order.warehouse_notes or '',
                 'delivery_person_comment': order.delivery_notes or '',
                 'amount_total': float(order.pos_order_id.amount_total) if order.pos_order_id else 0,
                 'order_lines': order_lines,
                 'create_date': order.create_date.isoformat(),
                 'assigned_at': order.assigned_date.isoformat() if order.assigned_date else None,
                 'in_transit_at': order.in_transit_date.isoformat() if order.in_transit_date else None,
                 'delivered_at': order.completed_date.isoformat() if order.completed_date else None,
                 'delivery_photo': order.delivery_photo.decode('utf-8') if order.delivery_photo else None,
                 'customer_rating': order.rating
            }
            
            return self._json_response(order_data)
            
        except Exception as e:
            _logger.error(f"Get order detail error: {str(e)}")
            return self._json_response(error=str(e), status=500)

    @http.route('/api/delivery/orders/<int:order_id>/update', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def update_order(self, order_id, **kwargs):
        """Update order status and info"""
        try:
            token = kwargs.get('token')
            action = kwargs.get('action')  # start_delivery, complete_delivery, add_comment
            comment = kwargs.get('comment', '')
            photo = kwargs.get('photo')  # base64 encoded
            
            delivery_person = self._validate_token(token)
            if not delivery_person:
                return self._json_response(error='Token inválido o expirado', status=401)
            
            order = request.env['pos.delivery.order'].sudo().browse(order_id)
            
            if not order.exists():
                return self._json_response(error='Pedido no encontrado', status=404)
            
            if order.delivery_person_id.id != delivery_person.id:
                return self._json_response(error='No tienes permiso para modificar este pedido', status=403)
            
            if action == 'start_delivery':
                if order.state != 'assigned':
                    return self._json_response(error='Este pedido no puede ser iniciado', status=400)
                
                order.action_start_transit()
                message = 'Entrega iniciada exitosamente'
                
            elif action == 'complete_delivery':
                if order.state != 'in_transit':
                    return self._json_response(error='Este pedido no está en tránsito', status=400)
                
                update_vals = {}
                if photo:
                    update_vals['delivery_photo'] = photo
                
                if update_vals:
                    order.write(update_vals)
                
                order.action_complete()
                message = 'Entrega completada exitosamente'
                
            elif action == 'add_comment':
                if not comment:
                    return self._json_response(error='El comentario no puede estar vacío', status=400)
                
                current_comment = order.delivery_notes or ''
                timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
                new_comment = f"[{timestamp}] {comment}"
                
                if current_comment:
                    updated_comment = f"{current_comment}\n{new_comment}"
                else:
                    updated_comment = new_comment
                
                order.write({'delivery_notes': updated_comment})
                message = 'Comentario agregado exitosamente'
                
            else:
                return self._json_response(error='Acción no válida', status=400)
            
            # Notify via bus (for websocket)
            request.env['bus.bus']._sendone(
                f'pos.delivery.order.{order.id}',
                'delivery_order_update',
                {
                    'order_id': order.id,
                    'state': order.state,
                    'updated_by': delivery_person.name,
                    'action': action
                }
            )
            
            return self._json_response({
                'message': message,
                'order': {
                    'id': order.id,
                    'state': order.state,
                    'state_label': dict(order._fields['state'].selection).get(order.state)
                }
            })
            
        except Exception as e:
            _logger.error(f"Update order error: {str(e)}")
            return self._json_response(error=str(e), status=500)

    @http.route('/api/delivery/qr-config', type='http', auth='user', methods=['GET'], csrf=False)
    def generate_qr_config(self):
        """Generate QR code configuration (called from POS backend)"""
        try:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            
            data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'server_url': base_url,
                    'api_version': '1.0',
                    'configured_at': datetime.now().isoformat()
                }
            }
            
            return Response(
                json.dumps(data, default=str),
                content_type='application/json',
                status=200
            )
            
        except Exception as e:
            _logger.error(f"QR config error: {str(e)}")
            error_data = {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            return Response(
                json.dumps(error_data, default=str),
                content_type='application/json',
                status=500
            )

