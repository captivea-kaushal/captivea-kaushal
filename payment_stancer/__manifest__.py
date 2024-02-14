{
    'name': "Payment Provider: Stancer",
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider covering and focused on the French market.",
    'depends': ['payment', 'account_accountant', 'sale_management'],
    'data': [
        'views/payment_stancer_templates.xml',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_transaction_extend.xml',
    ],

    'license': 'LGPL-3',
}
