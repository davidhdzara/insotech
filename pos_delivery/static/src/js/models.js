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

        // Add general note to the receipt
        if (this.general_note) {
            result.general_note = this.general_note;
            console.log("[POS_DELIVERY] ✅ General note sent to receipt:", result.general_note);
        }

        // Add creation date/time to the receipt
        if (this.creation_date) {
            const date = new Date(this.creation_date);
            result.creation_date = date.toLocaleString('es-CO', { 
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            console.log("[POS_DELIVERY] ✅ Creation date sent to receipt:", result.creation_date);
        }

        // Debug: Check if orderlines have customerNote
        console.log("[POS_DELIVERY] 🔍 Orderlines in receipt:", result.orderlines);
        if (result.orderlines && result.orderlines.length > 0) {
            result.orderlines.forEach((line, index) => {
                console.log(`[POS_DELIVERY] Line ${index}:`, {
                    product: line.product_name || line.productName,
                    customerNote: line.customerNote,
                    note: line.note
                });
            });
        }

        return result;
    },
});

