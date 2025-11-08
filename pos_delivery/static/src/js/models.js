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

        // Add general note to the receipt (preserve existing generalNote from parent)
        if (this.general_note) {
            result.generalNote = this.general_note;
            console.log("[POS_DELIVERY] ✅ General note sent to receipt:", result.generalNote);
        }

        // Add creation date/time to the receipt using date_order
        if (this.date_order) {
            // date_order is a string like "2025-11-08 03:43:39" in UTC
            // Need to parse it and adjust for timezone offset
            const utcDate = new Date(this.date_order + ' UTC'); // Parse as UTC
            result.creation_date = utcDate.toLocaleString('es-CO', { 
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true,
                timeZone: 'America/Bogota'
            });
            console.log("[POS_DELIVERY] ✅ Creation date sent to receipt:", result.creation_date);
            console.log("[POS_DELIVERY] 🔍 Original date_order:", this.date_order);
        }

        // Add internal notes to each orderline
        if (result.orderlines && this.lines) {
            result.orderlines.forEach((orderline, index) => {
                const posLine = this.lines[index];
                if (posLine && posLine.note) {
                    orderline.internalNote = posLine.note;
                    console.log(`[POS_DELIVERY] ✅ Added internal note to line ${index}:`, posLine.note);
                }
            });
        }

        return result;
    },
});

