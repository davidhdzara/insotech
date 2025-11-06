/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);

        // Add customer information to the receipt
        if (this.partner) {
            result.partner = {
                name: this.partner.name || '',
                street: this.partner.street || '',
                street2: this.partner.street2 || '',
                city: this.partner.city || '',
                state_id: this.partner.state_id ? this.partner.state_id[1] : '',
                zip: this.partner.zip || '',
                country_id: this.partner.country_id ? this.partner.country_id[1] : '',
                phone: this.partner.phone || '',
                mobile: this.partner.mobile || '',
            };
        }

        return result;
    },
});

