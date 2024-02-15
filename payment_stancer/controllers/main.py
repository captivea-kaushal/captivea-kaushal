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
            .filtered(lambda l: l.code == stancer_provider._get_code())
        last_transection_of_order = request.env['payment.transaction'].sudo().search(
            [('reference', 'ilike', order.name)], order="create_date desc", limit=1)
        stancer_payment_id = last_transection_of_order.provider_reference

        request_url = '/v1/checkout/' + stancer_payment_id
        payment_responce = stancer_provider._stancer_make_request(request_url, method='GET')
        if payment_responce.get('response') == '00' and payment_responce.get('status') not in ['canceled', 'disputed', 'failed', 'refused']:

            payment_values = {
                'amount': payment_responce['amount']/100,
                'payment_type': 'inbound',
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
            last_transection_of_order.state_message = 'Successful approval/completion or that VIP PIN verification is valid'
            payment.sudo().action_post()
        elif payment_responce.get('response') == '00' and payment_responce.get('status') in ['canceled', 'disputed', 'failed', 'refused']:
            last_transection_of_order.state_message = 'The payment has been refused [REASON : Dispute / Duplicated / Fraud]'
        elif payment_responce.get('response') == '05':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 05, Message: Do Not Honor]'
        elif payment_responce.get('response') == '51':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 05, Message: Insufficient Funds]'
        elif payment_responce.get('response') == '41':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 05, Message: Merchant should retain card (card reported lost)]'
        elif payment_responce.get('response') == '42':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 05, Message: Stolen Card / Duplicate processing]'
        elif payment_responce.get('response') == '01':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 01, Message: Refer to card issuer]'
        elif payment_responce.get('response') == '02':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 02, Message: Refer to card issuer, special condition]'
        elif payment_responce.get('response') == '03':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 03, Message: Invalid merchant or service provider]'
        elif payment_responce.get('response') == '04':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 04, Message: Pickup]'
        elif payment_responce.get('response') == '06':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 06, Message: General error]'
        elif payment_responce.get('response') == '07':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 07, Message: Pickup card, special condition (other than lost/stolen card)]'
        elif payment_responce.get('response') == '08':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 08, Message: Honor with identification]'
        elif payment_responce.get('response') == '09':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 09, Message: Request in progress]'
        elif payment_responce.get('response') == '10':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 10, Message: Partial approval]'
        elif payment_responce.get('response') == '11':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 11, Message: VIP approval]'
        elif payment_responce.get('response') == '12':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 12, Message: Invalid transaction]'
        elif payment_responce.get('response') == '13':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 13, Message: Invalid amount (currency conversion field overflow) or amount exceeds maximum for card program]'
        elif payment_responce.get('response') == '14':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 14, Message: Transaction not authorized / Invalid account number (no such number)]'
        elif payment_responce.get('response') == '15':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 15, Message: No such issuer]'
        elif payment_responce.get('response') == '16':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 16, Message: Insufficient funds]'
        elif payment_responce.get('response') == '17':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 17, Message: Customer cancellation]'
        elif payment_responce.get('response') == '19':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 19, Message: Re-enter transaction]'
        elif payment_responce.get('response') == '20':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 20, Message: Invalid response]'
        elif payment_responce.get('response') == '21':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 08, Message: No action taken (unable to back out prior transaction)]'
        elif payment_responce.get('response') == '22':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 22, Message: Suspected Malfunction]'
        elif payment_responce.get('response') == '25':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 25, Message: Unable to locate record in file, or account number is missing from the inquiry]'
        elif payment_responce.get('response') == '28':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 28, Message: File is temporarily unavailable]'
        elif payment_responce.get('response') == '30':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 30, Message: Format error]'
        elif payment_responce.get('response') == '43':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 43, Message: Merchant should retain card (card reported stolen)]'
        elif payment_responce.get('response') == '52':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 52, Message: No checking account]'
        elif payment_responce.get('response') == '53':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 53, Message: No savings account]'
        elif payment_responce.get('response') == '54':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 54, Message: Expired card]'
        elif payment_responce.get('response') == '55':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 55, Message: Incorrect PIN]'
        elif payment_responce.get('response') == '57':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 57, Message: Transaction not permitted to cardholder]'
        elif payment_responce.get('response') == '58':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 58, Message: Transaction not allowed at terminal]'
        elif payment_responce.get('response') == '59':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 59, Message: Suspected fraud]'
        elif payment_responce.get('response') == '61':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 61, Message: Activity amount limit exceeded]'
        elif payment_responce.get('response') == '62':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 62, Message: Restricted card (for example, in country exclusion table)]'
        elif payment_responce.get('response') == '63':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 63, Message: Security violation]'
        elif payment_responce.get('response') == '65':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 65, Message: Activity count limit exceeded]'
        elif payment_responce.get('response') == '68':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 68, Message: Response received too late]'
        elif payment_responce.get('response') == '75':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 75, Message: Allowable number of PIN-entry tries exceeded]'
        elif payment_responce.get('response') == '76':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 76, Message: Unable to locate previous message (no match on retrieval reference number)]'
        elif payment_responce.get('response') == '77':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 77, Message: Previous message located for a repeat or reversal, but repeat or reversal data are inconsistent with original message]'
        elif payment_responce.get('response') == '78':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 78, Message: ’Blocked, first used’—The transaction is from a new cardholder, and the card has not been properly unblocked.]'
        elif payment_responce.get('response') == '80':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 80, Message: Visa transactions: credit issuer unavailable. Private label and check acceptance: Invalid date]'
        elif payment_responce.get('response') == '81':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 81, Message: PIN cryptographic error found (error found by VIC security module during PIN decryption)]'
        elif payment_responce.get('response') == '82':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 82, Message: Negative CAM, dCVV, iCVV, or CVV results]'
        elif payment_responce.get('response') == '83':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 83, Message: Unable to verify PIN]'
        elif payment_responce.get('response') == '85':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 85, Message: No reason to decline a request for account number verification, address verification, CVV2 verification; or a credit voucher or merchandise return]'
        elif payment_responce.get('response') == '91':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 91, Message: Issuer unavailable or switch inoperative (STIP not applicable or available for this transaction)]'
        elif payment_responce.get('response') == '92':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 92, Message: Destination cannot be found for routing]'
        elif payment_responce.get('response') == '93':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 93, Message: Transaction cannot be completed, violation of law]'
        elif payment_responce.get('response') == '94':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 94, Message: Duplicate transmission]'
        elif payment_responce.get('response') == '95':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 95, Message: Reconcile error]'
        elif payment_responce.get('response') == '96':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 96, Message: System malfunction, System malfunction or certain field error conditions]'
        elif payment_responce.get('response') == 'A0':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: A0, Message: Authentication Required, you must do a card inserted payment with PIN code]'
        elif payment_responce.get('response') == 'A1':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: A1, Message: Authentication Required, you must do a 3-D Secure authentication]'
        elif payment_responce.get('response') == 'B1':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: B1, Message: Surcharge amount not permitted on Visa cards (U.S. acquirers only)]'
        elif payment_responce.get('response') == 'N0':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: N0, Message: Force STIP]'
        elif payment_responce.get('response') == 'N3':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: N3, Message: Cash service not available]'
        elif payment_responce.get('response') == 'N4':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: N4, Message: Cashback request exceeds issuer limit]'
        elif payment_responce.get('response') == 'N7':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: N7, Message: Decline for CVV2 failure]'
        elif payment_responce.get('response') == 'P2':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: P2, Message: Invalid biller information]'
        elif payment_responce.get('response') == 'P5':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: P5, Message: PIN change/unblock request declined]'
        elif payment_responce.get('response') == 'P6':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: P6, Message: Unsafe PIN]'
        elif payment_responce.get('response') == 'Q1':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: Q1, Message: Card authentication failed]'
        elif payment_responce.get('response') == 'R0':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: R0, Message: Stop payment order]'
        elif payment_responce.get('response') == 'R1':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: R1, Message: Revocation of authorization order]'
        elif payment_responce.get('response') == 'R3':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: R3, Message: Revocation of all authorizations order]'
        elif payment_responce.get('response') == 'XA':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: XA, Message: Forward to issuer]'
        elif payment_responce.get('response') == 'XD':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: XD, Message: Forward to issuer]'
        elif payment_responce.get('response') == 'Z1':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: Z1, Message: Offline-declined]'
        elif payment_responce.get('response') == 'Z3':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: Z3, Message: Unable to go online]'
        elif payment_responce.get('response') == '7810':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 7810, Message: Refusal count exceeded for this card / sepa]'
        elif payment_responce.get('response') == '7811':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 7811, Message: Exceeded payment volume for this card / sepa]'
        elif payment_responce.get('response') == '7840':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 7840, Message: Stolen or lost card]'
        elif payment_responce.get('response') == '7898':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 7898, Message: Bank server unavailable]'
        elif payment_responce.get('response') == '45':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 45, Message: Transaction disputed]'
        elif payment_responce.get('response') == '1040':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 1040, Message: Fraud; card Absent Environment]'
        elif payment_responce.get('response') == '1261':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 1261, Message: Duplicate processing]'
        elif payment_responce.get('response') == '4808':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 4808, Message: Requested/required authorization not obtained. Transaction not authorized]'
        elif payment_responce.get('response') == '4834':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 4834, Message: Duplicate processing]'
        elif payment_responce.get('response') == '4837':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 4837, Message: Fraudulent transaction; no cardholder authorization]'
        elif payment_responce.get('response') == '4853':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 4853, Message: Cardholder Dispute Defective/Not as Described]'
        elif payment_responce.get('response') == '4863':
            last_transection_of_order.state_message = 'The payment has been refused [Response CODE: 4863, Message: Cardholder does not recognize. Potential fraud]'

        return request.redirect('/payment/status')
