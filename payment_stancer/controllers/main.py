# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import base64
from odoo import http
import requests
from odoo.http import request

_logger = logging.getLogger(__name__)


class StancerController(http.Controller):
    _return_url = '/payment/stancer/return'

    @http.route(_return_url, type='http', methods=['GET'], auth='public', website=True)
    def stancer_return_from_checkout(self, **kwargs):
        """ Process the notification data sent by Stancer after redirection from checkout.

        :param dict data: The notification data.
        """
        order = request.website.sale_get_order()

        #TODO: TRY BELOW COMMENTED CODE TO GET LATEST TRANSACTION OF ORDER
        # orders_last_transection = order.get_portal_last_transaction()

        stancer_provider = request.env['payment.provider'].sudo().search([('code', '=', 'stancer')])
        payment_method_line = stancer_provider.journal_id.inbound_payment_method_line_ids \
            .filtered(lambda l: l.code == stancer_provider.code)
        last_transection_of_order = request.env['payment.transaction'].sudo().search(
            [('reference', 'ilike', order.name)], order="create_date desc", limit=1)
        stancer_payment_id = last_transection_of_order.provider_reference

        request_url = '/v1/checkout/' + stancer_payment_id
        payment_responce = stancer_provider._stancer_make_request(request_url, method='GET')
        print('\n\n\n payment_responce ------------>>>>>>>>>>> \n\n\n', payment_responce)
        if payment_responce.get('response') == '00' and payment_responce.get('status') not in ['canceled', 'disputed', 'failed', 'refused']:

            payment_values = {
                'amount': payment_responce['amount'] / 100,
                'payment_type': 'inbound' if payment_responce['amount']/100 > 0 else 'outbound',
                'currency_id': last_transection_of_order.currency_id.id,
                'partner_id': last_transection_of_order.partner_id.commercial_partner_id.id,
                'partner_type': 'customer',
                'journal_id': stancer_provider.journal_id.id,
                'company_id': stancer_provider.company_id.id,
                'payment_method_line_id': payment_method_line.id,
                'payment_transaction_id': last_transection_of_order.id,
                'ref': last_transection_of_order.reference,
            }

            payment = request.env['account.payment'].sudo().create(payment_values)

            last_transection_of_order.payment_id = payment.id
            last_transection_of_order.state = 'done'
            order.stancer_payment_id = stancer_payment_id
            last_transection_of_order.state_message = 'Successful approval/completion or that VIP PIN verification is valid'
            payment.sudo().action_post()
        elif payment_responce.get('response') == '00' and payment_responce.get('status') in ['canceled', 'disputed', 'failed', 'refused']:
            last_transection_of_order.state_message = 'The payment has been refused [ REASON : Dispute / Duplicated / Fraud]'
        elif payment_responce.get('response') == '05':
            last_transection_of_order.state_message = 'The payment has been refused [ REASON : Do Not Honor]'
        elif payment_responce.get('response') == '51':
            last_transection_of_order.state_message = 'The payment has been refused [ REASON : Insufficient Funds]'
        elif payment_responce.get('response') == '41':
            last_transection_of_order.state_message = 'The payment has been refused [ REASON : Lost Card]'
        elif payment_responce.get('response') == '42':
            last_transection_of_order.state_message = 'The payment has been refused [ REASON : Stolen Card]'


        return request.redirect('/payment/status')

    @http.route('/stancer/refund', type='http', methods=['GET', 'POST'], auth='public', website=True)
    def stancer_refund(self, **kwargs):
        sale_order = request.env['sale.order'].browse(int(kwargs.get('sale_order')))
        stancer_provider = request.env['payment.provider'].sudo().search([('code', '=', 'stancer')])
        payment_method_line = stancer_provider.journal_id.inbound_payment_method_line_ids \
            .filtered(lambda l: l.code == stancer_provider.code)
        sale_amount = kwargs.get('stancer_order_amount')
        stancer_payment = kwargs.get('stancer_order_transaction')
        headers = {
            'Content - Type': 'application / json',
            'Authorization': f'Basic {stancer_provider.stancer_key_secret}'
        }
        payload = {
            'payment' : stancer_payment,
            'amount': int(sale_amount) * 100
        }
        request_url = 'https://api.stancer.com/v1/refunds/'
        refund_request = requests.post(request_url, json=payload, headers=headers)
        refund_response = refund_request.json()
        if refund_response.get('id') and refund_response.get('status') == 'to_refund':
            sale_order.stancer_refund_id = refund_response.get('id')
            payment_values = {
                'amount': int(sale_amount),
                'payment_type': 'inbound' if int(sale_amount) > 0 else 'outbound',
                'currency_id': sale_order.currency_id.id,
                'partner_id': sale_order.partner_id.commercial_partner_id.id,
                'partner_type': 'customer',
                'journal_id': stancer_provider.journal_id.id,
                'company_id': stancer_provider.company_id.id,
                'payment_method_line_id': payment_method_line.id,
                # 'payment_transaction_id': last_transection_of_order.id,
                'ref': sale_order.name,
            }

        print(refund_response)
