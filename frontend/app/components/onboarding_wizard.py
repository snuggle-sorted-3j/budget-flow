"""Onboarding wizard layout components for BudgetFlow first-time setup."""
import dash_bootstrap_components as dbc
from dash import html, dcc


# ---------------------------------------------------------------------------
# Step definitions – the single source of truth for the wizard flow
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
        "subtitle": "Only for crypto or exotic currencies",
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
# Welcome modal
# ---------------------------------------------------------------------------

def create_welcome_modal() -> dbc.Modal:
    """Return the full-screen welcome modal shown before the tour starts."""
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
                [
                    html.Div(
                        steps_ui,
                        style={"borderTop": "1px solid #e2e8f0", "paddingTop": "12px"},
                    )
                ],
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
                        [
                            html.I(className="bi bi-play-fill me-2"),
                            "Start Tour",
                        ],
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
# Step panel (floating, bottom-right)
# ---------------------------------------------------------------------------

def _progress_dots(current_step: int) -> html.Div:
    """Render step progress indicator dots."""
    dots = []
    for s in ONBOARDING_STEPS:
        if s["num"] < current_step:
            cls = "onboarding-dot done"
        elif s["num"] == current_step:
            cls = "onboarding-dot active"
        else:
            cls = "onboarding-dot"
        dots.append(html.Div(className=cls))
    return html.Div(dots, className="onboarding-dots")


def create_step_panel(step_num: int, current_pathname: str) -> html.Div:
    """
    Build the floating step-guide panel for a given step number.

    Args:
        step_num: 1-based step index.
        current_pathname: The current URL pathname (from dcc.Location).
    """
    step = next((s for s in ONBOARDING_STEPS if s["num"] == step_num), None)
    if step is None:
        return html.Div()

    on_correct_page = current_pathname == step["path"]
    is_last = step_num == TOTAL_STEPS
    is_optional = not step["required"]

    # Navigate hint if user is on wrong page
    if not on_correct_page:
        content_body = html.Div(
            [
                html.P(step["description"], className="description"),
                html.Div(
                    [
                        html.I(className="bi bi-arrow-right-circle-fill"),
                        html.Span(
                            f" Navigate to the {step['title']} page using the sidebar, "
                            "then come back here — the guide will continue automatically.",
                        ),
                    ],
                    className="onboarding-navigate-hint",
                ),
                dbc.Button(
                    [html.I(className=f"bi bi-arrow-right me-1"), f" {step['nav_label']}"],
                    href=step["path"],
                    color="primary",
                    size="sm",
                    className="w-100",
                    external_link=False,
                ),
            ],
            className="onboarding-panel-body",
        )
    else:
        content_body = html.Div(
            [
                html.P(step["description"], className="description"),
                html.Div(
                    [
                        html.I(className="bi bi-pencil-square"),
                        html.Span(f" {step['instruction']}"),
                    ],
                    className="instruction-box d-flex align-items-start",
                ),
                html.Small(
                    [
                        html.I(className="bi bi-arrow-up me-1"),
                        "The highlighted fields above show what to fill in",
                    ],
                    className="text-muted d-block mb-1",
                    style={"fontSize": "0.78rem"},
                ),
            ],
            className="onboarding-panel-body",
        )

    # Footer buttons
    footer_left = _progress_dots(step_num)

    skip_btn = (
        dbc.Button(
            "Skip",
            id="onboarding-skip-btn",
            color="secondary",
            outline=True,
            size="sm",
            n_clicks=0,
        )
        if is_optional
        else html.Span()
    )

    next_label = (
        [html.I(className="bi bi-check-lg me-1"), "Finish Setup"]
        if is_last
        else [html.I(className="bi bi-arrow-right me-1"), "Done, Next Step"]
    )
    next_id = "onboarding-finish-btn" if is_last else "onboarding-next-btn"

    footer = html.Div(
        [
            footer_left,
            html.Div(
                [skip_btn, dbc.Button(next_label, id=next_id, color="primary", size="sm", n_clicks=0)],
                className="d-flex gap-2",
            ),
        ],
        className="onboarding-panel-footer",
    )

    # Dismiss (×) button in header
    dismiss_btn = dbc.Button(
        html.I(className="bi bi-x-lg"),
        id="onboarding-dismiss-btn",
        color="link",
        size="sm",
        n_clicks=0,
        style={"color": "rgba(255,255,255,0.7)", "padding": "0", "marginLeft": "auto"},
        title="Exit tour",
    )

    panel = html.Div(
        html.Div(
            [
                # Header
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    f"Step {step_num} of {TOTAL_STEPS}",
                                    className="step-badge",
                                ),
                                dismiss_btn,
                            ],
                            className="d-flex align-items-center",
                        ),
                        html.H5(step["title"]),
                        html.Div(step["subtitle"], className="subtitle"),
                    ],
                    className="onboarding-panel-header",
                ),
                content_body,
                footer,
            ]
        ),
        className="onboarding-panel",
    )

    return panel


# ---------------------------------------------------------------------------
# Stores and containers injected into the dashboard layout
# ---------------------------------------------------------------------------

def create_onboarding_layout_elements() -> list:
    """
    Return the list of Dash components to inject into the dashboard layout.
    Includes the persistent store, the welcome modal, backdrop, and panel container.
    """
    return [
        # Persists across browser sessions (localStorage)
        dcc.Store(
            id="onboarding-state",
            storage_type="local",
            data={"completed": False, "step": 0},
        ),
        # Dummy store used as output for the clientside highlight callback
        dcc.Store(id="onboarding-highlight-dummy", data=None),
        # Dark backdrop overlay
        html.Div(id="onboarding-backdrop", className="d-none"),
        # Welcome modal
        create_welcome_modal(),
        # Floating step panel (rendered by callback)
        html.Div(id="onboarding-panel-container"),
    ]
