/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

console.log("[POS_DELIVERY] models.js loaded - patching PosOrder");

patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);

        // Try to get partner using different methods
        let partner = this.partner || this.get_partner?.() || null;

        // Add customer information to the receipt
        if (partner) {
            result.partner = {
                name: partner.name || '',
                street: partner.street || '',
                street2: partner.street2 || '',
                city: partner.city || '',
                state_id: partner.state_id ? partner.state_id[1] : '',
                zip: partner.zip || '',
                country_id: partner.country_id ? partner.country_id[1] : '',
                phone: partner.phone || '',
                mobile: partner.mobile || '',
                vat: partner.vat || '',
                document_type: partner.document_type || '',
                document_number: partner.document_number || '',
            };
            console.log("[POS_DELIVERY] ✅ Partner data sent to receipt:", result.partner);
        } else {
            console.log("[POS_DELIVERY] ❌ No partner found for this order");
        }

        return result;
    },
});

