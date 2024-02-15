# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug import urls
import requests
import base64
from odoo import _, models, api, fields
from odoo.addons.payment_stancer.controllers.main import StancerController
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    refund_response = fields.Text(string='Refund Response', translate=True, readonly=True)
    refund_processed = fields.Boolean(string='Refund Done', readonly=True)
    stancer_refund_id = fields.Char(string='Stancer Refund Id', readonly=True)
    is_refund_transfer = fields.Boolean(string='Is Refund', readonly=True)
    stancer_refund_tx_id = fields.Many2one(comodel_name='payment.transaction', string='Stancer Refund Transaction',
                                           readonly=True)

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Stancer rendering values.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'stancer':
            return res

        _logger.warning(processing_values)
        # Initiate the payment and retrieve the payment link data.
        base_url = 'https://e7e6-2405-201-200f-18b4-a188-766b-3ca3-f17a.ngrok-free.app' #self.acquirer_id.get_base_url()

        payload = {
            'order_id': self.reference,
            'amount': self.amount * 100,
            'currency': 'usd',
            'auth': True,
            'return_url': urls.url_join(base_url, StancerController._return_url),
        }
        payment_link_data = self.acquirer_id._stancer_make_request('/v1/checkout', payload=payload, method='POST')

        #TODO: once this payment_link_data done then update return_url in dict of payment_link_data by adding ? and value of

        provider = self.env['payment.acquirer'].search([('provider', '=', 'stancer')], limit=1)
        payment_method_line = self.acquirer_id.journal_id.inbound_payment_method_line_ids\
            .filtered(lambda l: l.code == self.acquirer_id.provider)

        # payment_transaction = self.search([('reference', '=', self.reference), ('provider_code', '=', 'stancer')], limit=1)

        # payment_values = {
        #     'amount': abs(payment_link_data['amount']),
        #     'payment_type': 'inbound' if payment_link_data['amount'] > 0 else 'outbound',
        #     'currency_id': self.currency_id.id,
        #     'partner_id': self.partner_id.commercial_partner_id.id,
        #     'partner_type': 'customer',
        #     'journal_id': provider.journal_id.id,
        #     'company_id': provider.company_id.id,
        #     'payment_method_line_id': payment_method_line.id,
        #     'payment_transaction_id': payment_transaction.id,
        #     'ref': self.reference,
        # }
        #
        # payment = self.env['account.payment'].create(payment_values)
        # payment.action_post()

        self.update({'state': 'error', 'acquirer_reference': payment_link_data['id']}) #'state': 'done', 'payment_id': payment.id,
       
        _logger.warning(payment_link_data)

        rendering_values = {
            'api_url': urls.url_join('https://payment.stancer.com', '/{}/{}'.format(self.acquirer_id.stancer_key_client, payment_link_data['id'])),
        }

        _logger.warning(rendering_values)
        return rendering_values

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on transfer data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The transfer feedback data
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'stancer':
            return tx

        reference = data.get('reference')
        if data.get('provider'):
            tx = self.search([('reference', '=', reference), ('provider', '=', 'stancer')])
        if not tx:
            raise ValidationError(
                "Bread Transfer: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _handle_feedback_data(self, provider, data):
        """ Match the transaction with the feedback data, update its state and return it.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction
        :rtype: recordset of `payment.transaction`
        """
        super()._handle_feedback_data(provider, data)
        tx = self._get_tx_from_feedback_data(provider, data)
        tx._execute_callback()
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on transfer data.

        Note: self.ensure_one()

        :param dict data: The transfer feedback data
        :return: None
        """
        super()._process_feedback_data(data)
        if data.get('provider') != 'stancer':
            return

        for record in self:
            sales_orders = record.sale_order_ids.filtered(lambda so: so.state in ['draft', 'sent'])
            sales_orders.filtered(lambda so: so.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})

            if record.acquirer_id.provider == 'transfer' or record.acquirer_id.provider == 'stancer':
                for so in record.sale_order_ids:
                    so.reference = record._compute_sale_order_reference(so)
            # send order confirmation mail
            sales_orders._send_order_confirmation_mail()
            if record.provider != 'stancer':
                sales_orders.sudo().action_confirm()
                return
        payment_method_line = self.acquirer_id.journal_id.inbound_payment_method_line_ids \
            .filtered(lambda l: l.code == self.provider)
        payment_values = {
            'amount': abs(self.amount),  # A tx may have a negative amount, but a payment must >= 0
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_method_line_id': payment_method_line.id,
            # 'payment_method_line_id': 6,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'ref': self.reference,
        }
        payment = self.env['account.payment'].create(payment_values)
        payment.action_post()
        if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice') and \
                self.invoice_ids:
            domain = [
                ('parent_state', '=', 'posted'),
                ('account_internal_type', 'in', ('receivable', 'payable')),
                ('reconciled', '=', False),
            ]
            payment_lines = payment.line_ids.filtered_domain(domain)
            self.invoice_ids.action_post()
            self.invoice_ids.js_assign_outstanding_line(payment_lines.id)
            self.sale_order_ids.order_line._compute_invoice_status()
        if self.provider != 'stancer':
            return super()._process_feedback_data(data)

        _logger.info(
            "validated BREAD transfer payment for tx with reference %s: set as pending", self.reference
        )

    def action_stancer_refund(self):
        stancer_provider = self.acquirer_id
        payment_method_line = stancer_provider.journal_id.inbound_payment_method_line_ids \
            .filtered(lambda l: l.code == stancer_provider.provider)
        amount = self.amount * 100
        stancer_payment_id = self.acquirer_reference

        token = base64.b64encode(f"{stancer_provider.stancer_key_secret}:{''}".encode('utf-8')).decode("ascii")

        headers = {
            'Content - Type': 'application / json',
            'Authorization': f'Basic {token}'
        }
        payload = {
            'payment': stancer_payment_id,
            'amount': amount
        }

        request_url = 'https://api.stancer.com/v1/refunds/'
        refund_request = requests.post(request_url, json=payload, headers=headers)
        refund_response = refund_request.json()
        if 'id' in refund_response:
            self.stancer_refund_id = refund_response.get('id')
            self.refund_processed = True
            self.refund_response = str(refund_response)
            refund_tx = self.env['payment.transaction'].create({
                'acquirer_id': stancer_provider.id,
                'partner_id': self.partner_id.id,
                'reference': self.reference + ' Stancer Refund',
                'amount': -amount / 100,
                'state': 'done',
                'currency_id': self.currency_id.id,
                'acquirer_reference': refund_response.get('payment'),
                'stancer_refund_id': refund_response.get('id'),
                'is_refund_transfer': True,
                'refund_response': refund_response.get('status')
            })
            self.stancer_refund_tx_id = refund_tx.id
            payment_values = {
                'amount': amount / 100,
                'payment_type': 'outbound',
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'partner_type': 'customer',
                'journal_id': stancer_provider.journal_id.id,
                'company_id': stancer_provider.company_id.id,
                'payment_method_line_id': payment_method_line.id,
                'payment_transaction_id': refund_tx.id,
                'ref': self.reference + ' Stancer Refund'
            }

            payment = self.env['account.payment'].sudo().create(payment_values)
            refund_tx.payment_id = payment.id
            payment.action_post()

        else:
            raise ValidationError(_('Request issue occurred.\n Error Response : %s', str(refund_response)))
