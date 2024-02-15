# Part of Odoo. See LICENSE file for full copyright and licensing details.

# The currencies supported by Stancer, in ISO 4217 format.
# See https://flutterwave.com/us/support/general/what-are-the-currencies-accepted-on-flutterwave.
# Last website update: June 2022.
# Last seen online: 24 November 2022.
SUPPORTED_CURRENCIES = [
    'GBP',
    'CAD',
    'USD',
    'AUD',
    'EUR',
]

# Mapping of transaction states to Flutterwave payment statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending auth'],
    'done': ['successful'],
    'cancel': ['cancelled'],
    'error': ['failed'],
}

# The codes of the payment methods to activate when Flutterwave is activated.
DEFAULT_PAYMENT_METHODS_CODES = [
    # Primary payment methods.
    'stancer',
    # Brand payment methods.
    'visa',
    'mastercard',
    'jcb',
    'cb',
]

PAYMENT_METHODS_MAPPING = {
    'bank_transfer': 'banktransfer',
}
