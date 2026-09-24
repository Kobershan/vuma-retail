frappe.pages["vuma-setup"].on_page_load = function (wrapper) {
    new VumaSetupWizard(wrapper);
};


class VumaSetupWizard {
    constructor(wrapper) {
        this.wrapper = wrapper;

        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Vuma Setup",
            single_column: true,
        });

        this.state = {
            installation: {
                installation_id: "",
                installation_name: "",
                customer_name: "",
                company_count: 1,
                location_count: 1,
                licensed_user_count: 1,
                licensed_pos_count: 0,
            },

            companies: [],
            locations: [],
            mappings: [],
            modules: [],
            limits: {},
        };

        this.current_step = 0;
        this.field_groups = [];

        this.inject_styles();
        this.render_shell();
        this.render_welcome();
    }


    // ---------------------------------------------------------
    // Styling
    // ---------------------------------------------------------

    inject_styles() {
        $(`
            <style>
                .vuma-setup-shell {
                    max-width: 1180px;
                    margin: 32px auto;
                    padding: 0 20px 60px;
                    font-family: Inter, system-ui, -apple-system,
                        BlinkMacSystemFont, "Segoe UI", sans-serif;
                }

                .vuma-hero {
                    background:
                        linear-gradient(
                            135deg,
                            rgba(15,23,42,.99),
                            rgba(30,41,59,.97)
                        );
                    border-radius: 22px;
                    padding: 32px 36px;
                    color: white;
                    box-shadow: 0 18px 50px rgba(15,23,42,.18);
                    margin-bottom: 24px;
                }

                .vuma-brand {
                    display: flex;
                    align-items: center;
                    gap: 14px;
                }

                .vuma-logo {
                    width: 48px;
                    height: 48px;
                    border-radius: 14px;
                    background: white;
                    color: #0f172a;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 800;
                    font-size: 22px;
                    box-shadow: 0 8px 25px rgba(0,0,0,.16);
                }

                .vuma-brand-title {
                    font-size: 24px;
                    font-weight: 750;
                    letter-spacing: -.02em;
                }

                .vuma-brand-subtitle {
                    margin-top: 3px;
                    color: rgba(255,255,255,.65);
                    font-size: 13px;
                }

                .vuma-hero h1 {
                    margin: 30px 0 10px;
                    color: white;
                    font-size: 33px;
                    font-weight: 760;
                    letter-spacing: -.035em;
                }

                .vuma-hero p {
                    margin: 0;
                    max-width: 760px;
                    color: rgba(255,255,255,.72);
                    font-size: 14px;
                    line-height: 1.7;
                }

                .vuma-progress-card {
                    background: var(--card-bg, #fff);
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 18px;
                    padding: 22px 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 8px 30px rgba(15,23,42,.05);
                }

                .vuma-stepper {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    position: relative;
                }

                .vuma-stepper::before {
                    content: "";
                    position: absolute;
                    top: 17px;
                    left: 5%;
                    right: 5%;
                    height: 2px;
                    background: var(--border-color, #e5e7eb);
                    z-index: 0;
                }

                .vuma-step {
                    flex: 1;
                    position: relative;
                    z-index: 1;
                    text-align: center;
                }

                .vuma-step-circle {
                    width: 34px;
                    height: 34px;
                    margin: 0 auto 8px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 13px;
                    font-weight: 700;
                    border: 2px solid var(--border-color, #d1d5db);
                    background: var(--card-bg, #fff);
                    color: #64748b;
                    transition: .2s ease;
                }

                .vuma-step.active .vuma-step-circle {
                    background: #111827;
                    border-color: #111827;
                    color: white;
                }

                .vuma-step.complete .vuma-step-circle {
                    background: #15803d;
                    border-color: #15803d;
                    color: white;
                }

                .vuma-step-label {
                    font-size: 11px;
                    color: #64748b;
                }

                .vuma-step.active .vuma-step-label {
                    color: var(--text-color, #111827);
                    font-weight: 700;
                }

                .vuma-content-card {
                    background: var(--card-bg, #fff);
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 35px rgba(15,23,42,.06);
                }

                .vuma-content-header {
                    padding: 28px 30px 22px;
                    border-bottom: 1px solid var(--border-color, #e5e7eb);
                }

                .vuma-eyebrow {
                    font-size: 12px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: .08em;
                    color: #64748b;
                    margin-bottom: 8px;
                }

                .vuma-content-header h2 {
                    margin: 0;
                    font-size: 24px;
                    font-weight: 740;
                    color: var(--text-color, #111827);
                }

                .vuma-content-header p {
                    margin: 8px 0 0;
                    max-width: 760px;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #64748b;
                }

                .vuma-content-body {
                    padding: 30px;
                }

                .vuma-footer {
                    padding: 22px 30px;
                    border-top: 1px solid var(--border-color, #e5e7eb);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 15px;
                }

                .vuma-footer-right {
                    margin-left: auto;
                    display: flex;
                    gap: 10px;
                }

                .vuma-footer-note {
                    color: #64748b;
                    font-size: 12px;
                }

                .vuma-primary-btn,
                .vuma-secondary-btn {
                    appearance: none;
                    border-radius: 11px;
                    padding: 11px 20px;
                    font-size: 13px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: .18s ease;
                }

                .vuma-primary-btn {
                    border: 0;
                    background: #111827;
                    color: white;
                }

                .vuma-primary-btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 8px 22px rgba(15,23,42,.18);
                }

                .vuma-primary-btn:disabled {
                    opacity: .55;
                    cursor: not-allowed;
                    transform: none;
                }

                .vuma-secondary-btn {
                    background: transparent;
                    border: 1px solid var(--border-color, #d1d5db);
                    color: var(--text-color, #111827);
                }

                .vuma-info-grid {
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 16px;
                }

                .vuma-info-box {
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 16px;
                    padding: 20px;
                    background: var(--subtle-fg, #f8fafc);
                }

                .vuma-info-icon {
                    width: 38px;
                    height: 38px;
                    border-radius: 11px;
                    background: #111827;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    margin-bottom: 15px;
                }

                .vuma-info-box strong {
                    display: block;
                    margin-bottom: 5px;
                    font-size: 14px;
                }

                .vuma-info-box span {
                    display: block;
                    font-size: 12px;
                    line-height: 1.55;
                    color: #64748b;
                }

                .vuma-form-card {
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 16px;
                    padding: 22px;
                    margin-bottom: 18px;
                }

                .vuma-form-title {
                    font-size: 16px;
                    font-weight: 700;
                    margin-bottom: 18px;
                }

                .vuma-module-grid {
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 14px;
                }

                .vuma-module-card {
                    display: block;
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 15px;
                    padding: 17px;
                    cursor: pointer;
                    transition: .15s ease;
                    background: var(--card-bg, #fff);
                }

                .vuma-module-card:hover {
                    border-color: #94a3b8;
                    transform: translateY(-1px);
                }

                .vuma-module-card.selected {
                    border-color: #111827;
                    box-shadow: 0 0 0 1px #111827;
                }

                .vuma-module-top {
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                }

                .vuma-module-name {
                    font-size: 14px;
                    font-weight: 700;
                    flex: 1;
                }

                .vuma-module-code {
                    font-size: 10px;
                    font-weight: 700;
                    background: #e2e8f0;
                    color: #334155;
                    padding: 3px 7px;
                    border-radius: 6px;
                }

                .vuma-module-category {
                    margin-top: 9px;
                    font-size: 11px;
                    color: #64748b;
                }

                .vuma-module-flags {
                    margin-top: 10px;
                    font-size: 10px;
                    line-height: 1.5;
                    color: #64748b;
                }

                .vuma-mapping-table {
                    width: 100%;
                    border-collapse: collapse;
                }

                .vuma-mapping-table th,
                .vuma-mapping-table td {
                    border-bottom: 1px solid var(--border-color, #e5e7eb);
                    padding: 12px;
                    text-align: center;
                }

                .vuma-mapping-table th:first-child,
                .vuma-mapping-table td:first-child {
                    text-align: left;
                }

                .vuma-limit-card {
                    border: 1px solid var(--border-color, #e5e7eb);
                    border-radius: 16px;
                    margin-bottom: 15px;
                    padding: 20px;
                }

                .vuma-limit-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 16px;
                }

                .vuma-limit-header strong {
                    font-size: 15px;
                }

                .vuma-limit-fields {
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 14px;
                }

                .vuma-number-field label {
                    display: block;
                    font-size: 11px;
                    font-weight: 700;
                    color: #64748b;
                    margin-bottom: 6px;
                }

                .vuma-number-field input {
                    width: 100%;
                    border: 1px solid var(--border-color, #d1d5db);
                    border-radius: 9px;
                    padding: 9px 11px;
                    background: var(--control-bg, #fff);
                    color: var(--text-color, #111827);
                }

                .vuma-review-section {
                    margin-bottom: 28px;
                }

                .vuma-review-section h3 {
                    font-size: 15px;
                    margin-bottom: 12px;
                }

                .vuma-review-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }

                .vuma-review-table td,
                .vuma-review-table th {
                    border-bottom: 1px solid var(--border-color, #e5e7eb);
                    padding: 10px 8px;
                    text-align: left;
                }

                .vuma-success {
                    text-align: center;
                    padding: 55px 30px;
                }

                .vuma-success-icon {
                    width: 70px;
                    height: 70px;
                    margin: 0 auto 20px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #15803d;
                    color: white;
                    font-size: 30px;
                    font-weight: 700;
                }

                .vuma-success h2 {
                    font-size: 27px;
                    margin-bottom: 10px;
                }

                .vuma-success p {
                    max-width: 650px;
                    margin: 0 auto;
                    color: #64748b;
                    line-height: 1.6;
                }

                @media (max-width: 900px) {
                    .vuma-info-grid,
                    .vuma-module-grid,
                    .vuma-limit-fields {
                        grid-template-columns: 1fr;
                    }

                    .vuma-step-label {
                        display: none;
                    }
                }
            </style>
        `).appendTo(this.page.body);
    }


    // ---------------------------------------------------------
    // Shell
    // ---------------------------------------------------------

    render_shell() {
        $(`
            <div class="vuma-setup-shell">

                <div class="vuma-hero">
                    <div class="vuma-brand">
                        <div class="vuma-logo">V</div>

                        <div>
                            <div class="vuma-brand-title">
                                Vuma Retail
                            </div>

                            <div class="vuma-brand-subtitle">
                                Business platform configuration
                            </div>
                        </div>
                    </div>

                    <h1>Set up your Vuma installation</h1>

                    <p>
                        Configure companies, operating locations,
                        licensed modules and system limits.
                        Nothing is written to the live business
                        configuration until you confirm the final step.
                    </p>
                </div>

                <div class="vuma-progress-card">
                    <div class="vuma-stepper">

                        ${[
                            "Installation",
                            "Companies",
                            "Locations",
                            "Mapping",
                            "Modules",
                            "Limits",
                            "Review",
                        ].map((label, i) => `
                            <div class="vuma-step" data-step="${i + 1}">
                                <div class="vuma-step-circle">
                                    ${i + 1}
                                </div>

                                <div class="vuma-step-label">
                                    ${label}
                                </div>
                            </div>
                        `).join("")}

                    </div>
                </div>

                <div class="vuma-content-card"></div>

            </div>
        `).appendTo(this.page.body);
    }


    update_stepper(step) {
        this.current_step = step;

        $(".vuma-step").removeClass("active complete");

        $(".vuma-step").each(function () {
            const number = parseInt($(this).data("step"));

            if (number < step) {
                $(this).addClass("complete");
                $(this).find(".vuma-step-circle").text("✓");
            } else {
                $(this)
                    .find(".vuma-step-circle")
                    .text(number);
            }

            if (number === step) {
                $(this).addClass("active");
            }
        });
    }


    // ---------------------------------------------------------
    // Welcome
    // ---------------------------------------------------------

    render_welcome() {
        this.update_stepper(1);

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Vuma Retail
                </div>

                <h2>Welcome to Vuma Retail</h2>

                <p>
                    This wizard will build the initial business
                    structure for this installation.
                </p>
            </div>

            <div class="vuma-content-body">

                <div class="vuma-info-grid">

                    <div class="vuma-info-box">
                        <div class="vuma-info-icon">01</div>

                        <strong>Business structure</strong>

                        <span>
                            Configure legal companies and the
                            physical locations they operate from.
                        </span>
                    </div>

                    <div class="vuma-info-box">
                        <div class="vuma-info-icon">02</div>

                        <strong>Modules</strong>

                        <span>
                            Choose exactly which Vuma modules
                            this installation is entitled to use.
                        </span>
                    </div>

                    <div class="vuma-info-box">
                        <div class="vuma-info-icon">03</div>

                        <strong>Licence limits</strong>

                        <span>
                            Configure users, companies,
                            locations, employees and POS limits.
                        </span>
                    </div>

                </div>
            </div>

            <div class="vuma-footer">

                <div class="vuma-footer-note">
                    No business records have been created yet.
                </div>

                <button
                    class="vuma-primary-btn"
                    id="vuma-start-setup"
                >
                    Start Setup →
                </button>

            </div>
        `);

        $("#vuma-start-setup").on("click", () => {
            this.render_installation();
        });
    }


    // ---------------------------------------------------------
    // Step 1 — Installation
    // ---------------------------------------------------------

    render_installation() {
        this.update_stepper(1);

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 1 of 7
                </div>

                <h2>Installation Details</h2>

                <p>
                    Define the basic installation and its
                    overall licensed capacity.
                </p>
            </div>

            <div class="vuma-content-body">
                <div id="vuma-installation-form"></div>
            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-installation-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-installation-next"
                >
                    Continue →
                </button>

            </div>
        `);

        const fg = new frappe.ui.FieldGroup({
            body: $("#vuma-installation-form")[0],

            fields: [
                {
                    fieldtype: "Data",
                    fieldname: "installation_id",
                    label: "Installation ID",
                    description:
                        "Optional. If blank Vuma will generate one.",
                    default:
                        this.state.installation.installation_id,
                },
                {
                    fieldtype: "Data",
                    fieldname: "installation_name",
                    label: "Installation Name",
                    reqd: 1,
                    default:
                        this.state.installation.installation_name,
                },
                {
                    fieldtype: "Data",
                    fieldname: "customer_name",
                    label: "Customer Name",
                    reqd: 1,
                    default:
                        this.state.installation.customer_name,
                },
                {
                    fieldtype: "Section Break",
                    label: "Licensed Capacity",
                },
                {
                    fieldtype: "Int",
                    fieldname: "company_count",
                    label: "Number of Companies",
                    reqd: 1,
                    default:
                        this.state.installation.company_count || 1,
                },
                {
                    fieldtype: "Int",
                    fieldname: "location_count",
                    label: "Number of Locations",
                    reqd: 1,
                    default:
                        this.state.installation.location_count || 1,
                },
                {
                    fieldtype: "Int",
                    fieldname: "licensed_user_count",
                    label: "Licensed User Count",
                    reqd: 1,
                    default:
                        this.state.installation.licensed_user_count || 1,
                },
                {
                    fieldtype: "Int",
                    fieldname: "licensed_pos_count",
                    label: "Licensed POS Count",
                    default:
                        this.state.installation.licensed_pos_count || 0,
                },
            ],
        });

        fg.make();

        $("#vuma-installation-back").on("click", () => {
            this.render_welcome();
        });

        $("#vuma-installation-next").on("click", () => {
            const values = fg.get_values();

            if (!values) {
                return;
            }

            if (
                values.company_count < 1 ||
                values.location_count < 1 ||
                values.licensed_user_count < 1 ||
                values.licensed_pos_count < 0
            ) {
                frappe.msgprint(
                    __("Please enter valid installation limits.")
                );
                return;
            }

            this.state.installation = {
                ...values,
                company_count: Number(values.company_count),
                location_count: Number(values.location_count),
                licensed_user_count:
                    Number(values.licensed_user_count),
                licensed_pos_count:
                    Number(values.licensed_pos_count || 0),
            };

            this.render_companies();
        });
    }


    // ---------------------------------------------------------
    // Step 2 — Companies
    // ---------------------------------------------------------

    render_companies() {
        this.update_stepper(2);

        const count =
            this.state.installation.company_count;

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 2 of 7
                </div>

                <h2>Companies</h2>

                <p>
                    Add the ${count}
                    legal compan${count === 1 ? "y" : "ies"}
                    included in this installation.
                </p>
            </div>

            <div class="vuma-content-body">
                <div id="vuma-companies-container"></div>
            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-companies-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-companies-next"
                >
                    Continue →
                </button>

            </div>
        `);

        this.field_groups = [];

        for (let i = 0; i < count; i++) {
            const existing =
                this.state.companies[i] || {};

            const container_id =
                `vuma-company-${i}`;

            $("#vuma-companies-container").append(`
                <div class="vuma-form-card">
                    <div class="vuma-form-title">
                        Company ${i + 1}
                    </div>

                    <div id="${container_id}"></div>
                </div>
            `);

            const fg = new frappe.ui.FieldGroup({
                body: $(`#${container_id}`)[0],

                fields: [
                    {
                        fieldtype: "Data",
                        fieldname: "company_name",
                        label: "Company Name",
                        reqd: 1,
                        default:
                            existing.company_name || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "abbr",
                        label: "Company Abbreviation",
                        reqd: 1,
                        description:
                            "Example: ABC",
                        default:
                            existing.abbr || "",
                    },
                    {
                        fieldtype: "Link",
                        fieldname: "country",
                        label: "Country",
                        options: "Country",
                        reqd: 1,
                        default:
                            existing.country ||
                            "South Africa",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "default_currency",
                        label: "Default Currency",
                        options: "Currency",
                        reqd: 1,
                        default:
                            existing.default_currency ||
                            "ZAR",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "company_registration_no",
                        label: "Company Registration No",
                        description:
                            "Example: 2015/123456/07",
                        default:
                            existing.company_registration_no ||
                            "",
                    },
                    {
                        fieldtype: "Check",
                        fieldname: "is_vat_registered",
                        label: "VAT Registered?",
                        default:
                            existing.is_vat_registered ||
                            0,
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "tax_id",
                        label: "VAT Registration Number",
                        mandatory_depends_on:
                            "eval:doc.is_vat_registered",
                        depends_on:
                            "eval:doc.is_vat_registered",
                        default:
                            existing.tax_id || "",
                    },
                    {
                        fieldtype: "Attach Image",
                        fieldname: "company_logo",
                        label: "Company Logo",
                        description:
                            "PNG or SVG, transparent background works best",
                        default:
                            existing.company_logo || "",
                    },
                ],
            });

            fg.make();
            this.field_groups.push(fg);
        }

        $("#vuma-companies-back").on("click", () => {
            this.render_installation();
        });

        $("#vuma-companies-next").on("click", () => {
            const companies = [];

            for (const fg of this.field_groups) {
                const values = fg.get_values();

                if (!values) {
                    return;
                }

                companies.push(values);
            }

            const names = companies
                .map(c =>
                    c.company_name
                        .trim()
                        .toLowerCase()
                );

            if (
                new Set(names).size !== names.length
            ) {
                frappe.msgprint(
                    __("Company names must be unique.")
                );
                return;
            }

            this.state.companies = companies;
            this.render_locations();
        });
    }


    // ---------------------------------------------------------
    // Step 3 — Locations
    // ---------------------------------------------------------

    render_locations() {
        this.update_stepper(3);

        const count =
            this.state.installation.location_count;

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 3 of 7
                </div>

                <h2>Locations</h2>

                <p>
                    Add the physical operating locations
                    included in this installation.
                </p>
            </div>

            <div class="vuma-content-body">
                <div id="vuma-locations-container"></div>
            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-locations-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-locations-next"
                >
                    Continue →
                </button>

            </div>
        `);

        this.field_groups = [];

        for (let i = 0; i < count; i++) {
            const existing =
                this.state.locations[i] || {};

            const container_id =
                `vuma-location-${i}`;

            $("#vuma-locations-container").append(`
                <div class="vuma-form-card">
                    <div class="vuma-form-title">
                        Location ${i + 1}
                    </div>

                    <div id="${container_id}"></div>
                </div>
            `);

            const fg = new frappe.ui.FieldGroup({
                body: $(`#${container_id}`)[0],

                fields: [
                    {
                        fieldtype: "Data",
                        fieldname: "location_name",
                        label: "Location Name",
                        reqd: 1,
                        default:
                            existing.location_name || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "location_code",
                        label: "Location Code",
                        reqd: 1,
                        default:
                            existing.location_code || "",
                    },
                    {
                        fieldtype: "Check",
                        fieldname: "is_head_office",
                        label: "Head Office",
                        default:
                            existing.is_head_office ||
                            (i === 0 ? 1 : 0),
                    },
                    {
                        fieldtype: "Section Break",
                        label: "Address",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "address_line_1",
                        label: "Address Line 1",
                        default:
                            existing.address_line_1 || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "address_line_2",
                        label: "Address Line 2",
                        default:
                            existing.address_line_2 || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "city",
                        label: "City",
                        default:
                            existing.city || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "province",
                        label: "Province",
                        default:
                            existing.province || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "postal_code",
                        label: "Postal Code",
                        default:
                            existing.postal_code || "",
                    },
                    {
                        fieldtype: "Link",
                        fieldname: "country",
                        label: "Country",
                        options: "Country",
                        default:
                            existing.country ||
                            "South Africa",
                    },
                    {
                        fieldtype: "Section Break",
                        label: "Contact",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "phone",
                        label: "Phone",
                        default:
                            existing.phone || "",
                    },
                    {
                        fieldtype: "Data",
                        fieldname: "email",
                        label: "Email",
                        options: "Email",
                        default:
                            existing.email || "",
                    },
                    {
                        fieldtype: "Section Break",
                        label: "Capabilities",
                    },
                    {
                        fieldtype: "Check",
                        fieldname: "allow_pos",
                        label: "Allow POS",
                        default:
                            existing.allow_pos || 0,
                    },
                    {
                        fieldtype: "Check",
                        fieldname: "allow_stock",
                        label: "Allow Stock",
                        default:
                            existing.allow_stock ?? 1,
                    },
                    {
                        fieldtype: "Check",
                        fieldname: "allow_deliveries",
                        label: "Allow Deliveries",
                        default:
                            existing.allow_deliveries || 0,
                    },
                ],
            });

            fg.make();
            this.field_groups.push(fg);
        }

        $("#vuma-locations-back").on("click", () => {
            this.render_companies();
        });

        $("#vuma-locations-next").on("click", () => {
            const locations = [];

            for (const fg of this.field_groups) {
                const values = fg.get_values();

                if (!values) {
                    return;
                }

                locations.push(values);
            }

            const codes = locations.map(l =>
                l.location_code
                    .trim()
                    .toUpperCase()
            );

            if (
                new Set(codes).size !== codes.length
            ) {
                frappe.msgprint(
                    __("Location codes must be unique.")
                );
                return;
            }

            this.state.locations = locations;
            this.render_mapping();
        });
    }


    // ---------------------------------------------------------
    // Step 4 — Company ↔ Location mapping
    // ---------------------------------------------------------

    render_mapping() {
        this.update_stepper(4);

        const companies =
            this.state.companies;

        const locations =
            this.state.locations;

        let header = locations
            .map(location => `
                <th>
                    ${this.escape(location.location_name)}
                </th>
            `)
            .join("");

        let rows = companies
            .map((company, ci) => `
                <tr>
                    <td>
                        <strong>
                            ${this.escape(company.company_name)}
                        </strong>
                    </td>

                    ${locations.map((location, li) => {
                        const selected =
                            this.state.mappings.some(
                                m =>
                                    m.company_index === ci &&
                                    m.location_index === li
                            );

                        return `
                            <td>
                                <input
                                    type="checkbox"
                                    class="vuma-map-check"
                                    data-company="${ci}"
                                    data-location="${li}"
                                    ${selected ? "checked" : ""}
                                >
                            </td>
                        `;
                    }).join("")}
                </tr>
            `)
            .join("");

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 4 of 7
                </div>

                <h2>Company & Location Mapping</h2>

                <p>
                    Select which companies operate at
                    each physical location.
                </p>
            </div>

            <div class="vuma-content-body">

                <div style="overflow-x:auto;">
                    <table class="vuma-mapping-table">
                        <thead>
                            <tr>
                                <th>Company</th>
                                ${header}
                            </tr>
                        </thead>

                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>

            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-mapping-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-mapping-next"
                >
                    Continue →
                </button>

            </div>
        `);

        $("#vuma-mapping-back").on("click", () => {
            this.render_locations();
        });

        $("#vuma-mapping-next").on(
            "click",
            async () => {
                const mappings = [];

                $(".vuma-map-check:checked")
                    .each(function () {
                        mappings.push({
                            company_index:
                                Number(
                                    $(this)
                                        .data("company")
                                ),

                            location_index:
                                Number(
                                    $(this)
                                        .data("location")
                                ),
                        });
                    });

                for (
                    let i = 0;
                    i < companies.length;
                    i++
                ) {
                    if (
                        !mappings.some(
                            m =>
                                m.company_index === i
                        )
                    ) {
                        frappe.msgprint(
                            __(
                                `Company "${companies[i].company_name}" must be linked to at least one location.`
                            )
                        );

                        return;
                    }
                }

                for (
                    let i = 0;
                    i < locations.length;
                    i++
                ) {
                    if (
                        !mappings.some(
                            m =>
                                m.location_index === i
                        )
                    ) {
                        frappe.msgprint(
                            __(
                                `Location "${locations[i].location_name}" must be linked to at least one company.`
                            )
                        );

                        return;
                    }
                }

                this.state.mappings =
                    mappings;

                await this.render_modules();
            }
        );
    }


    // ---------------------------------------------------------
    // Step 5 — Modules
    // ---------------------------------------------------------

    async render_modules() {
        this.update_stepper(5);

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 5 of 7
                </div>

                <h2>Licensed Modules</h2>

                <p>
                    Select the modules included in
                    this customer's Vuma licence.
                </p>
            </div>

            <div class="vuma-content-body">
                <div style="
                    text-align:center;
                    padding:40px;
                    color:#64748b;
                ">
                    Loading module catalogue...
                </div>
            </div>
        `);

        let modules;

        try {
            modules = await frappe.db.get_list(
                "Vuma Module",
                {
                    filters: {
                        active: 1,
                    },

                    fields: [
                        "name",
                        "module_code",
                        "module_name",
                        "category",
                        "requires_user_count",
                        "requires_pos_count",
                        "requires_company_count",
                        "requires_location_count",
                        "requires_employee_count",
                    ],

                    order_by:
                        "category asc, module_name asc",

                    limit: 100,
                }
            );
        } catch (error) {
            console.error(error);

            frappe.msgprint(
                __("Unable to load Vuma modules.")
            );

            return;
        }

        this.available_modules = modules;

        const cards = modules
            .map(module => {
                const selected =
                    this.state.modules.some(
                        m =>
                            m.module_code ===
                            module.module_code
                    );

                const flags = [];

                if (module.requires_user_count)
                    flags.push("Users");

                if (module.requires_pos_count)
                    flags.push("POS");

                if (module.requires_company_count)
                    flags.push("Companies");

                if (module.requires_location_count)
                    flags.push("Locations");

                if (module.requires_employee_count)
                    flags.push("Employees");

                return `
                    <label
                        class="
                            vuma-module-card
                            ${selected ? "selected" : ""}
                        "
                    >

                        <div class="vuma-module-top">

                            <input
                                type="checkbox"
                                class="vuma-module-check"
                                data-code="${this.escape(
                                    module.module_code
                                )}"
                                ${selected ? "checked" : ""}
                            >

                            <div class="vuma-module-name">
                                ${this.escape(
                                    module.module_name
                                )}
                            </div>

                            <div class="vuma-module-code">
                                ${this.escape(
                                    module.module_code
                                )}
                            </div>

                        </div>

                        <div class="vuma-module-category">
                            ${this.escape(
                                module.category
                            )}
                        </div>

                        <div class="vuma-module-flags">
                            ${
                                flags.length
                                    ? `Licensed by: ${flags.join(", ")}`
                                    : "No additional limits"
                            }
                        </div>

                    </label>
                `;
            })
            .join("");

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 5 of 7
                </div>

                <h2>Licensed Modules</h2>

                <p>
                    Select every module the customer
                    is entitled to use.
                </p>
            </div>

            <div class="vuma-content-body">
                <div class="vuma-module-grid">
                    ${cards}
                </div>
            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-modules-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-modules-next"
                >
                    Continue →
                </button>

            </div>
        `);

        $(".vuma-module-check").on(
            "change",
            function () {
                $(this)
                    .closest(".vuma-module-card")
                    .toggleClass(
                        "selected",
                        this.checked
                    );
            }
        );

        $("#vuma-modules-back").on(
            "click",
            () => {
                this.render_mapping();
            }
        );

        $("#vuma-modules-next").on(
            "click",
            () => {
                const selected_codes = [];

                $(".vuma-module-check:checked")
                    .each(function () {
                        selected_codes.push(
                            $(this).data("code")
                        );
                    });

                if (!selected_codes.length) {
                    frappe.msgprint(
                        __(
                            "Select at least one module."
                        )
                    );
                    return;
                }

                this.state.modules =
                    this.available_modules.filter(
                        module =>
                            selected_codes.includes(
                                module.module_code
                            )
                    );

                this.render_limits();
            }
        );
    }


    // ---------------------------------------------------------
    // Step 6 — Module Limits
    // ---------------------------------------------------------

    render_limits() {
        this.update_stepper(6);

        const installation =
            this.state.installation;

        const cards = this.state.modules
            .map(module => {
                const current =
                    this.state.limits[
                        module.module_code
                    ] || {};

                const fields = [];

                if (module.requires_user_count) {
                    fields.push(
                        this.limit_field(
                            module.module_code,
                            "user_limit",
                            "User Limit",
                            current.user_limit ??
                                installation
                                    .licensed_user_count
                        )
                    );
                }

                if (module.requires_pos_count) {
                    fields.push(
                        this.limit_field(
                            module.module_code,
                            "pos_limit",
                            "POS Terminal Limit",
                            current.pos_limit ??
                                installation
                                    .licensed_pos_count
                        )
                    );
                }

                if (
                    module.requires_company_count
                ) {
                    fields.push(
                        this.limit_field(
                            module.module_code,
                            "company_limit",
                            "Company Limit",
                            current.company_limit ??
                                installation
                                    .company_count
                        )
                    );
                }

                if (
                    module.requires_location_count
                ) {
                    fields.push(
                        this.limit_field(
                            module.module_code,
                            "location_limit",
                            "Location Limit",
                            current.location_limit ??
                                installation
                                    .location_count
                        )
                    );
                }

                if (
                    module.requires_employee_count
                ) {
                    fields.push(
                        this.limit_field(
                            module.module_code,
                            "employee_limit",
                            "Employee Limit",
                            current.employee_limit ??
                                1
                        )
                    );
                }

                return `
                    <div class="vuma-limit-card">

                        <div class="vuma-limit-header">

                            <strong>
                                ${this.escape(
                                    module.module_name
                                )}
                            </strong>

                            <span class="vuma-module-code">
                                ${this.escape(
                                    module.module_code
                                )}
                            </span>

                        </div>

                        <div class="vuma-limit-fields">
                            ${
                                fields.length
                                    ? fields.join("")
                                    : `
                                        <div
                                            style="
                                                color:#64748b;
                                                font-size:12px;
                                            "
                                        >
                                            No additional
                                            limits required.
                                        </div>
                                    `
                            }
                        </div>

                    </div>
                `;
            })
            .join("");

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 6 of 7
                </div>

                <h2>Module Licence Limits</h2>

                <p>
                    Configure the allowed capacity
                    for each licensed module.
                </p>
            </div>

            <div class="vuma-content-body">
                ${cards}
            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-limits-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-limits-next"
                >
                    Review Setup →
                </button>

            </div>
        `);

        $("#vuma-limits-back").on(
            "click",
            () => {
                this.render_modules();
            }
        );

        $("#vuma-limits-next").on(
            "click",
            () => {
                const limits = {};

                for (
                    const module of
                    this.state.modules
                ) {
                    const code =
                        module.module_code;

                    limits[code] = {};

                    $(
                        `.vuma-limit-input[data-module="${code}"]`
                    ).each(function () {
                        const field =
                            $(this).data("field");

                        limits[code][field] =
                            Number(
                                $(this).val() || 0
                            );
                    });

                    const item = limits[code];

                    if (
                        item.user_limit >
                        installation.licensed_user_count
                    ) {
                        frappe.msgprint(
                            __(
                                `${module.module_name}: user limit cannot exceed the installation user limit.`
                            )
                        );

                        return;
                    }

                    if (
                        item.pos_limit >
                        installation.licensed_pos_count
                    ) {
                        frappe.msgprint(
                            __(
                                `${module.module_name}: POS limit cannot exceed the installation POS limit.`
                            )
                        );

                        return;
                    }

                    if (
                        item.company_limit >
                        installation.company_count
                    ) {
                        frappe.msgprint(
                            __(
                                `${module.module_name}: company limit cannot exceed the installation company count.`
                            )
                        );

                        return;
                    }

                    if (
                        item.location_limit >
                        installation.location_count
                    ) {
                        frappe.msgprint(
                            __(
                                `${module.module_name}: location limit cannot exceed the installation location count.`
                            )
                        );

                        return;
                    }
                }

                this.state.limits = limits;
                this.render_review();
            }
        );
    }


    limit_field(
        module_code,
        field,
        label,
        value
    ) {
        return `
            <div class="vuma-number-field">

                <label>
                    ${this.escape(label)}
                </label>

                <input
                    type="number"
                    min="0"
                    value="${Number(value || 0)}"
                    class="vuma-limit-input"
                    data-module="${this.escape(
                        module_code
                    )}"
                    data-field="${field}"
                >

            </div>
        `;
    }


    // ---------------------------------------------------------
    // Step 7 — Review
    // ---------------------------------------------------------

    render_review() {
        this.update_stepper(7);

        const installation =
            this.state.installation;

        const mapping_rows =
            this.state.mappings
                .map(mapping => {
                    const company =
                        this.state.companies[
                            mapping.company_index
                        ];

                    const location =
                        this.state.locations[
                            mapping.location_index
                        ];

                    return `
                        <tr>
                            <td>
                                ${this.escape(
                                    company.company_name
                                )}
                            </td>

                            <td>
                                ${this.escape(
                                    location.location_name
                                )}
                            </td>
                        </tr>
                    `;
                })
                .join("");

        const module_rows =
            this.state.modules
                .map(module => {
                    const limits =
                        this.state.limits[
                            module.module_code
                        ] || {};

                    const text = Object.entries(
                        limits
                    )
                        .filter(
                            ([, value]) =>
                                value !== undefined
                        )
                        .map(
                            ([key, value]) =>
                                `${key.replaceAll(
                                    "_",
                                    " "
                                )}: ${value}`
                        )
                        .join(" • ");

                    return `
                        <tr>
                            <td>
                                ${this.escape(
                                    module.module_code
                                )}
                            </td>

                            <td>
                                ${this.escape(
                                    module.module_name
                                )}
                            </td>

                            <td>
                                ${this.escape(
                                    text || "—"
                                )}
                            </td>
                        </tr>
                    `;
                })
                .join("");

        $(".vuma-content-card").html(`
            <div class="vuma-content-header">
                <div class="vuma-eyebrow">
                    Step 7 of 7
                </div>

                <h2>Review & Complete</h2>

                <p>
                    Review the configuration carefully.
                    Completing setup will create the live
                    Vuma installation records.
                </p>
            </div>

            <div class="vuma-content-body">

                <div class="vuma-review-section">

                    <h3>Installation</h3>

                    <table class="vuma-review-table">

                        <tr>
                            <td>Installation</td>
                            <td>
                                ${this.escape(
                                    installation
                                        .installation_name
                                )}
                            </td>
                        </tr>

                        <tr>
                            <td>Customer</td>
                            <td>
                                ${this.escape(
                                    installation
                                        .customer_name
                                )}
                            </td>
                        </tr>

                        <tr>
                            <td>Companies</td>
                            <td>
                                ${
                                    installation
                                        .company_count
                                }
                            </td>
                        </tr>

                        <tr>
                            <td>Locations</td>
                            <td>
                                ${
                                    installation
                                        .location_count
                                }
                            </td>
                        </tr>

                        <tr>
                            <td>Licensed Users</td>
                            <td>
                                ${
                                    installation
                                        .licensed_user_count
                                }
                            </td>
                        </tr>

                        <tr>
                            <td>Licensed POS</td>
                            <td>
                                ${
                                    installation
                                        .licensed_pos_count
                                }
                            </td>
                        </tr>

                    </table>
                </div>


                <div class="vuma-review-section">

                    <h3>Companies</h3>

                    <table class="vuma-review-table">
                        <thead>
                            <tr>
                                <th>Company</th>
                                <th>Abbreviation</th>
                                <th>Currency</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${this.state.companies
                                .map(c => `
                                    <tr>
                                        <td>
                                            ${this.escape(
                                                c.company_name
                                            )}
                                        </td>

                                        <td>
                                            ${this.escape(
                                                c.abbr
                                            )}
                                        </td>

                                        <td>
                                            ${this.escape(
                                                c.default_currency
                                            )}
                                        </td>
                                    </tr>
                                `)
                                .join("")}
                        </tbody>
                    </table>
                </div>


                <div class="vuma-review-section">

                    <h3>Locations</h3>

                    <table class="vuma-review-table">
                        <thead>
                            <tr>
                                <th>Location</th>
                                <th>Code</th>
                                <th>City</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${this.state.locations
                                .map(l => `
                                    <tr>
                                        <td>
                                            ${this.escape(
                                                l.location_name
                                            )}
                                        </td>

                                        <td>
                                            ${this.escape(
                                                l.location_code
                                            )}
                                        </td>

                                        <td>
                                            ${this.escape(
                                                l.city || "—"
                                            )}
                                        </td>
                                    </tr>
                                `)
                                .join("")}
                        </tbody>
                    </table>
                </div>


                <div class="vuma-review-section">

                    <h3>
                        Company ↔ Location Mapping
                    </h3>

                    <table class="vuma-review-table">
                        <thead>
                            <tr>
                                <th>Company</th>
                                <th>Location</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${mapping_rows}
                        </tbody>
                    </table>
                </div>


                <div class="vuma-review-section">

                    <h3>Licensed Modules</h3>

                    <table class="vuma-review-table">
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Module</th>
                                <th>Limits</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${module_rows}
                        </tbody>
                    </table>
                </div>

            </div>

            <div class="vuma-footer">

                <button
                    class="vuma-secondary-btn"
                    id="vuma-review-back"
                >
                    ← Back
                </button>

                <button
                    class="vuma-primary-btn"
                    id="vuma-complete-setup"
                >
                    Complete Vuma Setup
                </button>

            </div>
        `);

        $("#vuma-review-back").on(
            "click",
            () => {
                this.render_limits();
            }
        );

        $("#vuma-complete-setup").on(
            "click",
            () => {
                this.complete_setup();
            }
        );
    }


    // ---------------------------------------------------------
    // Complete
    // ---------------------------------------------------------

    async complete_setup() {
        const button =
            $("#vuma-complete-setup");

        button
            .prop("disabled", true)
            .text("Completing Setup...");

        try {
            const result =
                await frappe.call({
                    method:
                        "vuma.vuma_retail.page.vuma_setup.vuma_setup.complete_setup",

                    args: {
                        payload:
                            JSON.stringify(
                                this.state
                            ),
                    },

                    freeze: true,

                    freeze_message:
                        __(
                            "Creating Vuma installation..."
                        ),
                });

            this.render_success(
                result.message
            );
        } catch (error) {
            console.error(error);

            button
                .prop("disabled", false)
                .text(
                    "Complete Vuma Setup"
                );
        }
    }


    render_success(result) {
        $(".vuma-step")
            .removeClass("active")
            .addClass("complete");

        $(".vuma-step-circle").text("✓");

        $(".vuma-content-card").html(`
            <div class="vuma-success">

                <div class="vuma-success-icon">
                    ✓
                </div>

                <h2>
                    Vuma setup complete
                </h2>

                <p>
                    The installation, companies,
                    locations, company mappings and
                    module entitlements have been created.
                </p>

                <div style="margin-top:25px;">
                    <strong>
                        Installation ID:
                    </strong>

                    ${this.escape(
                        result.installation_id
                    )}
                </div>

                <div style="margin-top:28px;">

                    <button
                        class="vuma-primary-btn"
                        id="vuma-finish"
                    >
                        Go to Vuma Retail
                    </button>

                </div>

            </div>
        `);

        $("#vuma-finish").on(
            "click",
            () => {
                frappe.set_route(
                    "Workspaces",
                    "Vuma Retail"
                );
            }
        );
    }


    // ---------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------

    escape(value) {
        return frappe.utils.escape_html(
            String(value ?? "")
        );
    }
}
