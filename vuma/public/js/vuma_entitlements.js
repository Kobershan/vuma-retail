frappe.provide("vuma");

vuma.entitlements = {
    get_modules() {
        return frappe.boot?.vuma?.modules || [];
    },

    is_enabled(module_code) {
        const code = String(module_code || "")
            .trim()
            .toUpperCase();

        return this.get_modules().includes(code);
    },

    require(module_code) {
        const code = String(module_code || "")
            .trim()
            .toUpperCase();

        if (!this.is_enabled(code)) {
            frappe.throw(
                __("This Vuma module is not licensed for this installation.")
            );
        }

        return true;
    },

    filter_items(items) {
        return (items || []).filter((item) => {
            if (!item.module_code) {
                return true;
            }

            return this.is_enabled(item.module_code);
        });
    }
};

