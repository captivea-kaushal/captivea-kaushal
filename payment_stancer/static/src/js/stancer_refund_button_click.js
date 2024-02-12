/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.StancerRefund = publicWidget.Widget.extend({
    selector: '#sale_order_sidebar_stancer_refund_button',
    events: {
        "click a.stancer_refund": '_StancerRefund',
    },

    _StancerRefund: async function (ev) {

        $.ajax({
            url: "/stancer/refund",
            type: 'GET',
            data: {
                sale_order: $("#stancer_order")[0].value,
                stancer_order_amount: $('#stancer_order_amount')[0].value,
                stancer_order_transaction: $('#stancer_order_transaction')[0].value
            },
            success: (response) =>{
                console.log('-------->', response)
            },
        });
//        .then((result) => {
//            console.log(result)
//        });
//        await this._rpc({
//            route: '/stancer/refund',
//            params: {
//                sale_order: $("#stancer_order")[0].value,
//                stancer_order_amount: $('#stancer_order_amount')[0].value,
//                stancer_order_transaction: $('#stancer_order_transaction')[0].value
//            }
//        })
//            window.location.reload(true);
    },

});
