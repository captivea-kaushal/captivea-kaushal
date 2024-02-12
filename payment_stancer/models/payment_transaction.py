# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug.urls import url_join
from werkzeug import urls

from odoo import _, models

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_stancer.controllers.main import StancerController
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Stancer rendering values.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'stancer':
            return res

        _logger.warning(processing_values)
        # Initiate the payment and retrieve the payment link data.
        base_url = 'https://d186-2405-201-200f-18b4-9b5b-74f8-cdc2-8398.ngrok-free.app/' #self.provider_id.get_base_url()

        payload = {
            'order_id': self.reference,
            'amount': self.amount * 100,
            'currency': 'usd',
            'auth': True,
            'return_url': urls.url_join(base_url, StancerController._return_url),
        }
        payment_link_data = self.provider_id._stancer_make_request('/v1/checkout', payload=payload, method='POST')

        #TODO: once this payment_link_data done then update return_url in dict of payment_link_data by adding ? and value of

        provider = self.env['payment.provider'].search([('code', '=', 'stancer')], limit=1)
        payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids\
            .filtered(lambda l: l.code == self.provider_id.code)

        payment_transaction = self.search([('reference', '=', self.reference), ('provider_code', '=', 'stancer')], limit=1)

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

        self.update({'state': 'error', 'provider_reference': payment_link_data['id']}) #'state': 'done', 'payment_id': payment.id,
       
        _logger.warning(payment_link_data)

        rendering_values = {
            'api_url': urls.url_join('https://payment.stancer.com', '/{}/{}'.format(self.provider_id.stancer_key_client, payment_link_data['id'])),
        }

        _logger.warning(rendering_values)
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from Paytabs.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from Paytabs notification.
        :return: The transaction matching the reference.
        """
        _logger.warning(notification_data)
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        _logger.warning(notification_data)
        if provider_code != 'stancer':
            return tx
        reference = notification_data.get('order_id', False)
        if not reference:
            raise ValidationError(_("Stancer: No reference found."))
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'stancer')])
        if not tx:
            raise ValidationError(
                _("Stancer: No transaction found matching reference"
                  "%s.") % reference)
        _logger.warning(tx)
        return tx
