from odoo import models, fields


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    stancer_payment_id = fields.Char(string='Stancer Payment Id')
    stancer_refund_id = fields.Char(string='Stancer Refund Id')
