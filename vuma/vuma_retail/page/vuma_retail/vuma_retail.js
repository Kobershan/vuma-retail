frappe.pages["vuma-retail"].on_page_load = function (wrapper) {
    new VumaRetailDashboard(wrapper);
};


class VumaRetailDashboard {
    constructor(wrapper) {
        this.wrapper = wrapper;

        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Vuma Retail",
            single_column: true,
        });

        this.module_catalogue = [
            {
                code: "ACC",
                name: "Accounting & Finance",
                description: "Finance, ledgers, journals, receivables and payables.",
                route: "/app/accounting",
            },
            {
                code: "SAL",
                name: "Sales",
                description: "Customers, quotations, orders and invoicing.",
                route: "/app/selling",
            },
            {
                code: "PUR",
                name: "Purchasing",
                description: "Suppliers, purchase orders and procurement.",
                route: "/app/buying",
            },
            {
                code: "INV",
                name: "Inventory",
                description: "Stock, warehouses, transfers and inventory control.",
                route: "/app/stock",
            },
            {
                code: "POS",
                name: "Point of Sale",
                description: "Retail till operations and POS management.",
                route: "/app/point-of-sale",
            },
            {
                code: "MFG",
                name: "Manufacturing",
                description: "BOMs, production planning and manufacturing.",
                route: "/app/manufacturing",
            },
            {
                code: "SRV",
                name: "Services",
                description: "Service operations and customer service workflows.",
                route: null,
            },
            {
                code: "PRJ",
                name: "Projects",
                description: "Projects, tasks, costing and delivery tracking.",
                route: "/app/projects",
            },
            {
                code: "AST",
                name: "Assets",
                description: "Asset registers, depreciation and lifecycle management.",
                route: "/app/assets",
            },
            {
                code: "CRM",
                name: "CRM",
                description: "Leads, opportunities and customer relationships.",
                route: "/app/crm",
            },
            {
                code: "HRP",
                name: "HR & Payroll",
                description: "Employees, leave, attendance and payroll.",
                route: "/app/hr",
            },
            {
                code: "QMS",
                name: "Quality Management",
                description: "Quality checks, inspections and compliance.",
                route: "/app/quality",
            },
            {
                code: "MNT",
                name: "Maintenance",
                description: "Maintenance schedules and equipment servicing.",
                route: "/app/maintenance",
            },
            {
                code: "ECM",
                name: "E-commerce",
                description: "Online commerce and digital sales channels.",
                route: null,
            },
            {
                code: "LOY",
                name: "Loyalty",
                description: "Customer loyalty, points and rewards.",
                route: null,
            },
            {
                code: "SUP",
                name: "Supplier Connect",
                description: "Supplier collaboration and connected procurement.",
                route: null,
            },
            {
                code: "MOB",
                name: "Mobile Management",
                description: "Mobile access for authorised management users.",
                route: null,
            },
            {
                code: "MCO",
                name: "Multi-Company",
                description: "Manage multiple legal entities from one Vuma installation.",
                route: null,
            },
            {
                code: "RPT",
                name: "Advanced Reporting",
                description: "Cross-module reporting, KPIs and analytics.",
                route: null,
            },
            {
                code: "API",
                name: "API & Integrations",
                description: "External integrations and API access.",
                route: null,
            },
            {
                code: "AUD",
                name: "Audit & Compliance",
                description: "Audit trails, controls and compliance monitoring.",
                route: null,
            },
        ];

        this.inject_styles();
        this.render();
    }


    inject_styles() {
        $(`
            <style>
                .vuma-dashboard {
                    max-width: 1280px;
                    margin: 28px auto 60px;
                    padding: 0 22px;
                }

                .vuma-dashboard-hero {
                    border-radius: 22px;
                    padding: 30px 34px;
                    margin-bottom: 24px;
                    background: linear-gradient(
                        135deg,
                        rgba(15, 23, 42, 0.99),
                        rgba(30, 41, 59, 0.97)
                    );
                    color: white;
                    box-shadow: 0 18px 50px rgba(15, 23, 42, .16);
                }

                .vuma-dashboard-hero h1 {
                    margin: 0 0 8px;
                    color: white;
                    font-size: 31px;
                    font-weight: 760;
                    letter-spacing: -.03em;
                }

                .vuma-dashboard-hero p {
                    margin: 0;
                    color: rgba(255,255,255,.72);
                    font-size: 14px;
                    line-height: 1.6;
                }

                .vuma-status-row {
                    display: grid;
                    grid-template-columns: repeat(4, minmax(0, 1fr));
                    gap: 14px;
                    margin-bottom: 24px;
                }

                .vuma-status-card {
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 16px;
                    background: var(--card-bg, #fff);
                    padding: 18px;
                }

                .vuma-status-label {
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: .07em;
                    color: #64748b;
                    margin-bottom: 7px;
                    font-weight: 700;
                }

                .vuma-status-value {
                    font-size: 18px;
                    font-weight: 740;
                    color: var(--text-color, #111827);
                }

                .vuma-section-title {
                    margin: 4px 0 14px;
                    font-size: 18px;
                    font-weight: 740;
                }

                .vuma-module-grid {
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 15px;
                }

                .vuma-module-card {
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 17px;
                    background: var(--card-bg, #fff);
                    padding: 20px;
                    cursor: pointer;
                    transition: .17s ease;
                    min-height: 150px;
                    display: flex;
                    flex-direction: column;
                }

                .vuma-module-card:hover {
                    transform: translateY(-2px);
                    border-color: #94a3b8;
                    box-shadow: 0 10px 26px rgba(15, 23, 42, .08);
                }

                .vuma-module-top {
                    display: flex;
                    justify-content: space-between;
                    gap: 10px;
                    align-items: flex-start;
                }

                .vuma-module-name {
                    font-size: 16px;
                    font-weight: 740;
                    margin-bottom: 7px;
                }

                .vuma-module-code {
                    font-size: 10px;
                    font-weight: 700;
                    background: #e2e8f0;
                    color: #334155;
                    border-radius: 7px;
                    padding: 4px 7px;
                }

                .vuma-module-description {
                    color: #64748b;
                    font-size: 12px;
                    line-height: 1.55;
                    flex: 1;
                }

                .vuma-module-footer {
                    margin-top: 14px;
                    font-size: 11px;
                    color: #475569;
                    font-weight: 700;
                }

                .vuma-empty {
                    border: 1px dashed var(--border-color, #d1d5db);
                    border-radius: 16px;
                    padding: 35px;
                    text-align: center;
                    color: #64748b;
                }

                @media (max-width: 1000px) {
                    .vuma-module-grid {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }

                    .vuma-status-row {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }
                }

                @media (max-width: 650px) {
                    .vuma-module-grid,
                    .vuma-status-row {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        `).appendTo(this.page.body);
    }


    render() {
        const vuma_boot = frappe.boot?.vuma || {};

        const installation = vuma_boot.installation || {};

        const enabled_codes = new Set(
            vuma_boot.modules || []
        );

        const enabled_modules = this.module_catalogue.filter(
            module => enabled_codes.has(module.code)
        );

        const module_cards = enabled_modules.map(
            module => this.module_card(module)
        ).join("");

        $(`
            <div class="vuma-dashboard">

                <div class="vuma-dashboard-hero">
                    <h1>Vuma Retail</h1>

                    <p>
                        ${this.escape(
                            installation.name || "Vuma Installation"
                        )}
                        ${
                            installation.customer
                                ? `• ${this.escape(installation.customer)}`
                                : ""
                        }
                    </p>
                </div>

                <div class="vuma-status-row">

                    <div class="vuma-status-card">
                        <div class="vuma-status-label">
                            Installation ID
                        </div>

                        <div class="vuma-status-value">
                            ${this.escape(
                                installation.id || "Not configured"
                            )}
                        </div>
                    </div>

                    <div class="vuma-status-card">
                        <div class="vuma-status-label">
                            Licence Status
                        </div>

                        <div class="vuma-status-value">
                            ${this.escape(
                                installation.licence_status || "Unknown"
                            )}
                        </div>
                    </div>

                    <div class="vuma-status-card">
                        <div class="vuma-status-label">
                            Licensed Modules
                        </div>

                        <div class="vuma-status-value">
                            ${enabled_modules.length}
                        </div>
                    </div>

                    <div class="vuma-status-card">
                        <div class="vuma-status-label">
                            Integrity
                        </div>

                        <div class="vuma-status-value">
                            ${this.escape(
                                installation.integrity_status || "Unknown"
                            )}
                        </div>
                    </div>

                </div>

                <div class="vuma-section-title">
                    Licensed Modules
                </div>

                ${
                    enabled_modules.length
                        ? `
                            <div class="vuma-module-grid">
                                ${module_cards}
                            </div>
                        `
                        : `
                            <div class="vuma-empty">
                                No licensed modules are available
                                for this installation.
                            </div>
                        `
                }

            </div>
        `).appendTo(this.page.body);

        this.bind_clicks();
    }


    module_card(module) {
        return `
            <div
                class="vuma-module-card"
                data-module="${this.escape(module.code)}"
            >
                <div class="vuma-module-top">

                    <div>
                        <div class="vuma-module-name">
                            ${this.escape(module.name)}
                        </div>
                    </div>

                    <div class="vuma-module-code">
                        ${this.escape(module.code)}
                    </div>

                </div>

                <div class="vuma-module-description">
                    ${this.escape(module.description)}
                </div>

                <div class="vuma-module-footer">
                    Open module →
                </div>
            </div>
        `;
    }


    bind_clicks() {
        $(".vuma-module-card").on("click", event => {
            const code = $(event.currentTarget).data("module");

            const module = this.module_catalogue.find(
                item => item.code === code
            );

            if (!module) {
                return;
            }

            vuma.entitlements.require(code);

            if (!module.route) {
                frappe.msgprint({
                    title: __(module.name),
                    message: __(
                        "This Vuma module is licensed, but its Vuma workspace has not been built yet."
                    ),
                    indicator: "blue",
                });

                return;
            }

            window.location.href = module.route;
        });
    }


    escape(value) {
        return frappe.utils.escape_html(
            String(value ?? "")
        );
    }
}
