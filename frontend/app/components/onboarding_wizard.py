"""Onboarding wizard layout components for BudgetFlow first-time setup."""
import dash_bootstrap_components as dbc
from dash import html, dcc


# ---------------------------------------------------------------------------
# Step definitions – single source of truth for the wizard flow
# ---------------------------------------------------------------------------

ONBOARDING_STEPS = [
    {
        "num": 1,
        "title": "Add Your Accounts",
        "subtitle": "Bank accounts & cash wallets",
        "description": (
            "Accounts are the foundation of BudgetFlow. "
            "Add every account you want to track — savings, current, cash, etc."
        ),
        "instruction": (
            "Enter the Account Name, choose the Type (Bank or Cash), "
            "select a Currency, and enter your current Opening Balance. "
            "Then click Add Account."
        ),
        "path": "/dashboard/accounts",
        "nav_label": "Go to Accounts",
        "highlight_ids": [
            "account-name-input",
            "account-type-select",
            "account-currency-select",
            "account-opening-balance",
        ],
        "required": True,
    },
    {
        "num": 2,
        "title": "Set Up Currencies",
        "subtitle": "Only needed for crypto or exotic currencies",
        "description": (
            "Common world currencies (USD, EUR, GBP, PLN, …) are already built in. "
            "Only add a custom currency here if you need crypto or an unlisted one."
        ),
        "instruction": (
            "Enter a Ticker (e.g. BTC) and the full Name (e.g. Bitcoin). "
            "Tick Default if this should be your primary currency. "
            "Click Add Currency when done."
        ),
        "path": "/dashboard/currencies",
        "nav_label": "Go to Currencies",
        "highlight_ids": ["currency-ticker", "currency-name"],
        "required": False,
    },
    {
        "num": 3,
        "title": "Create Expense Categories",
        "subtitle": "Organise your spending",
        "description": (
            "Categories help you see where your money goes. "
            "Common examples: Groceries, Rent, Transport, Entertainment."
        ),
        "instruction": (
            "Enter a Category Name and optionally add an emoji as an icon. "
            "Create as many categories as you need, then click Add Category."
        ),
        "path": "/dashboard/categories",
        "nav_label": "Go to Categories",
        "highlight_ids": ["category-name-input", "category-description-input"],
        "required": False,
    },
    {
        "num": 4,
        "title": "Create Your First Period",
        "subtitle": "Define a budget monitoring period",
        "description": (
            "A period is a date range — usually one month — for which you'll "
            "record income, expenses, and run reconciliation."
        ),
        "instruction": (
            "Enter a Period Name (e.g. 'January 2026'), set the Start Date "
            "and End Date, then click Create Period."
        ),
        "path": "/dashboard/periods",
        "nav_label": "Go to Periods",
        "highlight_ids": ["period-name-input", "period-start-date", "period-end-date"],
        "required": True,
    },
]

TOTAL_STEPS = len(ONBOARDING_STEPS)


# ---------------------------------------------------------------------------
# Welcome modal (IDs are permanent — modal is always in layout)
# ---------------------------------------------------------------------------

def create_welcome_modal() -> dbc.Modal:
    """Return the welcome modal shown before the tour starts."""
    steps_ui = []
    for step in ONBOARDING_STEPS:
        icon_cls = "required" if step["required"] else "optional"
        icon_name = (
            "bi-wallet2" if step["num"] == 1
            else "bi-currency-exchange" if step["num"] == 2
            else "bi-tags" if step["num"] == 3
            else "bi-calendar3"
        )
        badge = (
            html.Span("Required", className="badge bg-primary ms-2 fw-normal")
            if step["required"]
            else html.Span("Optional", className="badge bg-success ms-2 fw-normal")
        )
        steps_ui.append(
            html.Div(
                [
                    html.Div(
                        html.I(className=f"bi {icon_name}"),
                        className=f"step-icon {icon_cls}",
                    ),
                    html.Div(
                        [
                            html.H6([f"Step {step['num']}: {step['title']}", badge]),
                            html.P(step["subtitle"]),
                        ],
                        className="step-text",
                    ),
                ],
                className="onboarding-welcome-step",
            )
        )

    return dbc.Modal(
        [
            dbc.ModalHeader(
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-lightning-charge-fill me-2",
                                    style={"color": "#3b82f6"},
                                ),
                                html.Span(
                                    "BudgetFlow",
                                    className="fw-bold",
                                    style={"fontSize": "1.4rem"},
                                ),
                            ],
                            className="d-flex align-items-center mb-1",
                        ),
                        html.H4(
                            "Welcome! Let's get you set up.",
                            className="mb-0 fw-bold",
                            style={"fontSize": "1.25rem"},
                        ),
                        html.P(
                            "This quick tour walks you through the four setup steps "
                            "so BudgetFlow is ready to use in minutes.",
                            className="text-muted mb-0 mt-1",
                            style={"fontSize": "0.88rem"},
                        ),
                    ]
                ),
                close_button=False,
                className="border-0 pb-0",
            ),
            dbc.ModalBody(
                html.Div(
                    steps_ui,
                    style={"borderTop": "1px solid #e2e8f0", "paddingTop": "12px"},
                ),
                className="pt-2",
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Skip Setup",
                        id="onboarding-skip-all-btn",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="me-auto",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-play-fill me-2"), "Start Tour"],
                        id="onboarding-start-btn",
                        color="primary",
                        n_clicks=0,
                    ),
                ],
                className="border-0",
            ),
        ],
        id="onboarding-welcome-modal",
        is_open=False,
        centered=True,
        size="md",
        backdrop="static",
        keyboard=False,
    )


# ---------------------------------------------------------------------------
# Persistent step panel — ALL IDs live here permanently.
# The callback updates content and shows/hides the panel via style.
# ---------------------------------------------------------------------------

def create_persistent_step_panel() -> html.Div:
    """
    Return the floating step-guide panel with ALL button IDs baked in.
    Hidden by default (style display:none). Callbacks update its content
    and toggle visibility — they never re-create the element.
    """
    header = html.Div(
        [
            html.Div(
                [
                    html.Span(id="onboarding-step-badge", className="step-badge"),
                    # Dismiss × button — always present
                    dbc.Button(
                        html.I(className="bi bi-x-lg"),
                        id="onboarding-dismiss-btn",
                        color="link",
                        size="sm",
                        n_clicks=0,
                        style={
                            "color": "rgba(255,255,255,0.7)",
                            "padding": "0",
                            "marginLeft": "auto",
                        },
                        title="Exit tour",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            html.H5(id="onboarding-panel-title", className="mb-0 mt-1"),
            html.Div(id="onboarding-panel-subtitle", className="subtitle"),
        ],
        className="onboarding-panel-header",
    )

    body = html.Div(id="onboarding-panel-body", className="onboarding-panel-body")

    footer = html.Div(
        [
            # Progress dots — updated by callback
            html.Div(id="onboarding-dots-container", className="onboarding-dots"),
            html.Div(
                [
                    # Skip button — hidden for required steps
                    dbc.Button(
                        "Skip",
                        id="onboarding-skip-btn",
                        color="secondary",
                        outline=True,
                        size="sm",
                        n_clicks=0,
                        style={"display": "none"},
                    ),
                    # Next button — hidden on last step
                    dbc.Button(
                        [html.I(className="bi bi-arrow-right me-1"), "Done, Next Step"],
                        id="onboarding-next-btn",
                        color="primary",
                        size="sm",
                        n_clicks=0,
                    ),
                    # Finish button — hidden until last step
                    dbc.Button(
                        [html.I(className="bi bi-check-lg me-1"), "Finish Setup"],
                        id="onboarding-finish-btn",
                        color="success",
                        size="sm",
                        n_clicks=0,
                        style={"display": "none"},
                    ),
                ],
                className="d-flex gap-2",
            ),
        ],
        className="onboarding-panel-footer",
    )

    return html.Div(
        html.Div([header, body, footer]),
        id="onboarding-panel",
        className="onboarding-panel",
        style={"display": "none"},
    )


# ---------------------------------------------------------------------------
# Elements injected once into the dashboard layout
# ---------------------------------------------------------------------------

def create_onboarding_layout_elements() -> list:
    """
    Return Dash components to inject into the dashboard layout once.
    All interactive IDs are permanently present — nothing is created dynamically.
    """
    return [
        # Persists across browser sessions (localStorage)
        dcc.Store(
            id="onboarding-state",
            storage_type="local",
            data={"completed": False, "step": 0},
        ),
        # Dummy output for clientside highlight callback
        dcc.Store(id="onboarding-highlight-dummy", data=None),
        # Dark backdrop overlay
        html.Div(id="onboarding-backdrop", className="d-none"),
        # Welcome modal (all IDs permanent)
        create_welcome_modal(),
        # Floating step panel (all button IDs permanent)
        create_persistent_step_panel(),
    ]
