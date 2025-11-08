# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class DeliverySettlementReport(models.TransientModel):
    _name = 'delivery.settlement.report'
    _description = 'Reporte de Liquidación de Domicilios'

    date = fields.Date(string='Fecha de Liquidación', required=True, default=fields.Date.today)
    delivery_person_id = fields.Many2one('res.users', string='Domiciliario')
    report_text = fields.Text(string='Reporte', readonly=True)

    def action_calculate(self):
        """Calculate and display settlement report"""
        self.ensure_one()
        
        # Get orders
        domain = [
            ('state', 'in', ['completed', 'delivered']),
            ('create_date', '>=', fields.Datetime.to_string(datetime.combine(self.date, datetime.min.time()))),
            ('create_date', '<=', fields.Datetime.to_string(datetime.combine(self.date, datetime.max.time()))),
        ]
        
        if self.delivery_person_id:
            domain.append(('delivery_person_id', '=', self.delivery_person_id.id))
        
        orders = self.env['pos.delivery.order'].search(domain)
        
        if not orders:
            self.report_text = 'No hay órdenes para esta fecha'
        else:
            # Group by delivery person
            delivery_persons = orders.mapped('delivery_person_id')
            
            lines = []
            lines.append('=' * 120)
            lines.append(f'LIQUIDACIÓN DE DOMICILIOS - {self.date.strftime("%d/%m/%Y")}')
            lines.append('=' * 120)
            lines.append('')
            
            for person in delivery_persons:
                person_orders = orders.filtered(lambda o: o.delivery_person_id == person)
                
                # Calculate delivery costs
                delivery_cost_cash = sum(o.delivery_cost for o in person_orders if o.delivery_payment_method == 'cash')
                delivery_cost_transfer = sum(o.delivery_cost for o in person_orders if o.delivery_payment_method == 'transfer')
                delivery_cost_total = delivery_cost_cash + delivery_cost_transfer
                
                # Group by payment method from POS order
                payment_methods = {}
                for order in person_orders:
                    if order.pos_order_id:
                        for payment in order.pos_order_id.payment_ids:
                            method_name = payment.payment_method_id.name
                            if method_name not in payment_methods:
                                payment_methods[method_name] = {'count': 0, 'amount': 0.0}
                            payment_methods[method_name]['count'] += 1
                            payment_methods[method_name]['amount'] += payment.amount
                
                lines.append(f'DOMICILIARIO: {person.name}')
                lines.append('-' * 120)
                lines.append(f'{"Método de Pago":<25} {"Cant.":<10} {"Total Órdenes":<20} {"Dom. Efectivo":<20} {"Dom. Transfer.":<20} {"Total Dom.":<15}')
                lines.append('-' * 120)
                
                for method_name, data in payment_methods.items():
                    lines.append(
                        f'{method_name:<25} '
                        f'{data["count"]:<10} '
                        f'${data["amount"]:>18,.2f} '
                        f'${delivery_cost_cash:>18,.2f} '
                        f'${delivery_cost_transfer:>18,.2f} '
                        f'${delivery_cost_total:>13,.2f}'
                    )
                
                lines.append('')
            
            lines.append('=' * 120)
            self.report_text = '\n'.join(lines)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.settlement.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

