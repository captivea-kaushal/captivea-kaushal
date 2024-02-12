{
    'name': "Payment Provider: Stancer",
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider covering and focused on the French market.",
    'depends': ['payment', 'account_accountant', 'sale_management'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_stancer_templates.xml',
        'views/sale_order_portal_extend.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_stancer/static/src/js/stancer_refund_button_click.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

    'license': 'LGPL-3',
}
