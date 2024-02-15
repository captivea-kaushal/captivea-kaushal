{
    'name': "Payment Provider: Stancer",
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider covering and focused on the French market.",
    'depends': ['payment', 'account_accountant', 'sale_management'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_stancer_templates.xml',
        'views/payment_provider_views.xml',
        'views/payment_transaction_extend.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

    'license': 'LGPL-3',
}
