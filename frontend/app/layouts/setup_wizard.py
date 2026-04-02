"""Setup wizard layout for first-time users."""
from dash import html, dcc
import dash_bootstrap_components as dbc


def _step_indicator(current: int) -> html.Div:
    steps = [
        (1, "Default Currency"),
        (2, "First Account"),
        (3, "First Period"),
        (4, "Done"),
    ]
    items = []
    for num, label in steps:
        if num < current:
            color, icon = "success", "bi-check-circle-fill"
        elif num == current:
            color, icon = "primary", "bi-circle-fill"
        else:
            color, icon = "secondary", "bi-circle"
        items.append(
            html.Div(
                [
                    html.I(className=f"bi {icon} text-{color} fs-4"),
                    html.Small(label, className=f"d-block text-{color} mt-1"),
                ],
                className="text-center flex-fill",
            )
        )
    return html.Div(items, className="d-flex justify-content-between mb-4")


def _step1_currency(currencies: list) -> dbc.Card:
    options = [{"label": f"{c['ticker']} — {c['name']}", "value": c["id"]} for c in currencies]
    default_val = next((c["id"] for c in currencies if c.get("is_default")), None)
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Step 1: Choose Your Default Currency", className="mb-3"),
                html.P(
                    "Select the primary currency you use for most transactions. "
                    "You can add more currencies later.",
                    className="text-muted",
                ),
                dbc.Label("Default Currency"),
                dcc.Dropdown(
                    id="wizard-currency-select",
                    options=options,
                    value=default_val,
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Button(
                    "Next: Create Account",
                    id="wizard-step1-next",
                    color="primary",
                    className="w-100",
                    disabled=default_val is None,
                ),
            ]
        )
    )


def _step2_account() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Step 2: Add Your First Account", className="mb-3"),
                html.P(
                    "Enter the bank or cash account you'll track. You can add more later.",
                    className="text-muted",
                ),
                dbc.Label("Account Name *"),
                dbc.Input(
                    id="wizard-account-name",
                    placeholder="e.g. Main Bank Account",
                    className="mb-2",
                ),
                dbc.Label("Account Type"),
                dcc.Dropdown(
                    id="wizard-account-type",
                    options=[
                        {"label": "Bank Account", "value": "BANK"},
                        {"label": "Cash", "value": "CASH"},
                    ],
                    value="BANK",
                    clearable=False,
                    className="mb-2",
                ),
                dbc.Label("Opening Balance"),
                dbc.Input(
                    id="wizard-account-balance",
                    type="number",
                    value=0,
                    min=0,
                    step=0.01,
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button("Back", id="wizard-step2-back", color="secondary", outline=True),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Create Account",
                                id="wizard-step2-next",
                                color="primary",
                            ),
                        ),
                    ],
                    justify="between",
                ),
                html.Div(id="wizard-account-error", className="text-danger mt-2"),
            ]
        )
    )


def _step3_period() -> dbc.Card:
    from datetime import date, timedelta
    today = date.today()
    first_of_month = today.replace(day=1)
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Step 3: Create Your First Period", className="mb-3"),
                html.P(
                    "Periods represent your paycheck cycles. Define the date range for your first one.",
                    className="text-muted",
                ),
                dbc.Label("Period Name *"),
                dbc.Input(
                    id="wizard-period-name",
                    value=today.strftime("%B %Y"),
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Start Date"),
                                dbc.Input(
                                    id="wizard-period-start",
                                    type="date",
                                    value=first_of_month.isoformat(),
                                    className="mb-2",
                                ),
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Label("End Date"),
                                dbc.Input(
                                    id="wizard-period-end",
                                    type="date",
                                    value=today.isoformat(),
                                    className="mb-2",
                                ),
                            ]
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button("Back", id="wizard-step3-back", color="secondary", outline=True),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Create Period",
                                id="wizard-step3-next",
                                color="primary",
                            ),
                        ),
                    ],
                    justify="between",
                    className="mt-2",
                ),
                html.Div(id="wizard-period-error", className="text-danger mt-2"),
            ]
        )
    )


def _step4_done() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(className="bi bi-check-circle-fill text-success", style={"fontSize": "4rem"}),
                        html.H4("You're all set!", className="mt-3"),
                        html.P(
                            "Your account and first period are ready. Head to the dashboard to start tracking.",
                            className="text-muted",
                        ),
                        dbc.Button(
                            "Go to Dashboard",
                            id="wizard-finish-btn",
                            color="success",
                            size="lg",
                            className="mt-2",
                            href="/dashboard",
                        ),
                    ],
                    className="text-center py-3",
                )
            ]
        )
    )


def create_setup_wizard_layout(step: int = 1, currencies: list = None) -> html.Div:
    """Return the full setup wizard page for the given step."""
    currencies = currencies or []
    step_content = {
        1: _step1_currency(currencies),
        2: _step2_account(),
        3: _step3_period(),
        4: _step4_done(),
    }.get(step, _step1_currency(currencies))

    return html.Div(
        dbc.Container(
            [
                html.H2("Welcome to BudgetFlow", className="text-center mb-1"),
                html.P(
                    "Let's get you set up in a few quick steps.",
                    className="text-center text-muted mb-4",
                ),
                _step_indicator(step),
                dcc.Store(id="wizard-step-store", data=step),
                dcc.Store(id="wizard-currency-id-store", data=None),
                step_content,
            ],
            className="py-5",
            style={"maxWidth": "560px"},
        ),
        className="min-vh-100 d-flex align-items-center justify-content-center bg-light",
    )
