import dash
from dash import Input, Output, State, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils.api_client import APIClient
from utils.ui_helpers import format_currency, get_amount_class


def _difference_explanation(currency, difference):
    """Return contextual explanation of the reconciliation gap."""
    abs_diff = abs(difference)
    if difference > 0:
        return dbc.Alert(
            [
                html.I(className="bi bi-info-circle me-2"),
                html.Strong(f"You have {format_currency(abs_diff)} {currency} LESS than recorded. "),
                "Possible reasons: small cash purchases without receipts, ATM withdrawals, or missing expenses.",
                html.Br(),
                html.Small(
                    "Add an 'Untracked Expenses' entry below, or review your expense list.",
                    className="text-muted"
                ),
            ],
            color="warning",
            className="mt-3 mb-2",
        )
    else:
        return dbc.Alert(
            [
                html.I(className="bi bi-info-circle me-2"),
                html.Strong(f"You have {format_currency(abs_diff)} {currency} MORE than recorded. "),
                "Possible reasons: forgot to record an income source, or over-recorded an expense.",
            ],
            color="info",
            className="mt-3 mb-2",
        )


def create_recon_currency_card(summary, period_id=None, period_status=None):
    """Create a polished card for a single currency reconciliation."""
    currency = summary.get("currency_ticker", "")
    starting = float(summary.get("starting_balance", 0))
    expected = float(summary.get("expected_balance", 0))
    actual = float(summary.get("actual_balance", 0))
    difference = float(summary.get("difference", 0))
    is_balanced = summary.get("is_balanced", False)

    status_pill_class = "status-balanced" if is_balanced else "status-difference"
    badge_text = "BALANCED ✓" if is_balanced else f"UNRECONCILED GAP: {format_currency(difference)}"

    diff_border = "card-balanced" if is_balanced else "card-unbalanced"
    diff_text_class = get_amount_class(difference)

    # Action section: quick-balance button when positive difference (expected > actual → add expense)
    action_section = []
    if not is_balanced and period_status != "FINALIZED":
        action_section.append(_difference_explanation(currency, difference))
        if difference > 0:
            action_section.append(
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-2"), f"Add Untracked Expense ({format_currency(difference)} {currency})"],
                    id={"type": "quick-balance-btn", "currency": currency},
                    color="warning",
                    size="sm",
                    className="mt-1 mb-2",
                )
            )

    finalized_badge = []
    if period_status == "FINALIZED":
        finalized_badge = [dbc.Badge("FINALIZED", color="secondary", className="ms-2")]

    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span([currency] + finalized_badge, className="currency-ticker float-end"),
                    html.Div("Reconciliation Status", className="text-muted small fw-bold text-uppercase mb-3"),

                    html.Div([
                        html.Span(badge_text, className=f"status-pill {status_pill_class} fs-6"),
                    ], className="mb-4"),

                    dbc.Row([
                        dbc.Col([
                            html.Div("Starting", className="text-muted x-small fw-bold text-uppercase"),
                            html.Div(format_currency(starting), className="fw-bold"),
                        ]),
                        dbc.Col([
                            html.Div("Expected", className="text-muted x-small fw-bold text-uppercase"),
                            html.Div(format_currency(expected), className="fw-bold"),
                        ]),
                        dbc.Col([
                            html.Div("Actual", className="text-muted x-small fw-bold text-uppercase"),
                            html.Div(format_currency(actual), className="fw-bold"),
                        ]),
                    ], className="mb-3"),

                    html.Hr(className="opacity-25"),

                    html.Div([
                        html.Div("Reconciliation Gap", className="text-muted small fw-bold text-uppercase"),
                        html.Div(format_currency(difference, show_sign=True),
                                className=f"recon-diff-xl {diff_text_class}"),
                    ], className="text-center py-2"),

                    *action_section,
                ])
            ])
        ], className=f"dashboard-card {diff_border} mb-4"),
        md=12, lg=6, xl=4
    )


def register_reconciliation_callbacks(app):
    """Register reconciliation callbacks."""
    
    api_client = APIClient()

    @app.callback(
        [
            Output("recon-content-container", "style"),
            Output("snapshot-date-display", "children"),
            Output("snapshots-table-container", "children"),
            Output("recon-summary-container", "children"),
            Output("recon-balanced-store", "data"),
        ],
        [Input("current-period-id", "data"), Input("session-store", "data")],
        prevent_initial_call=True,
    )
    def show_recon_content(period_id, session_data):
        """Show reconciliation content when period is selected."""
        if not period_id or not session_data or "token" not in session_data:
            return {"display": "none"}, "", "", dash.no_update, dash.no_update

        token = session_data["token"]
        api_client.set_token(token)

        # Get period details
        period_response = api_client.get(f"/periods/{period_id}")
        if "error" in period_response:
            return {"display": "none"}, "", "", [], False

        snapshot_date = period_response.get("snapshot_date", "")
        
        # Get accounts for this user
        accounts_response = api_client.get("/accounts/")
        if "error" in accounts_response:
            return {"display": "block"}, f"Snapshot Date: {snapshot_date}", "Error loading accounts", [], False

        # Get existing snapshots
        snapshots_response = api_client.get(f"/periods/{period_id}/snapshots")
        existing_snapshots = {}
        if "error" not in snapshots_response:
            existing_snapshots = {s.get("account_id"): s.get("actual_balance", 0) for s in snapshots_response}

        # Create snapshot input table
        snapshot_rows = []
        for account in accounts_response:
            account_id = account.get("id", "")
            account_name = account.get("account_name", "")
            currency_code = account.get("currency_code", "")
            existing_balance = existing_snapshots.get(account_id, 0)
            
            snapshot_rows.append(
                dbc.Row(
                    [
                        dbc.Col(html.Div(account_name, className="fw-bold"), md=4),
                        dbc.Col(html.Div(currency_code), md=2),
                        dbc.Col(
                            dbc.Input(
                                id={"type": "snapshot-balance", "account_id": account_id},
                                type="number",
                                step="0.01",
                                value=existing_balance,
                                placeholder="0.00",
                            ),
                            md=4,
                        ),
                    ],
                    className="mb-2 align-items-center",
                )
            )

        snapshot_table = html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.Div("Account", className="fw-bold"), md=4),
                        dbc.Col(html.Div("Currency", className="fw-bold"), md=2),
                        dbc.Col(html.Div("Actual Balance", className="fw-bold"), md=4),
                    ],
                    className="mb-3",
                ),
            ] + snapshot_rows
        )

        date_display = dbc.Alert(
            [html.Strong("Snapshot Date: "), snapshot_date],
            color="light",
        )

        return {"display": "block"}, date_display, snapshot_table, [], False

    @app.callback(
        [
            Output("snapshot-message", "children"),
            Output("snapshot-message", "color"),
            Output("snapshot-message", "is_open"),
        ],
        [Input("save-snapshots-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State({"type": "snapshot-balance", "account_id": dash.ALL}, "id"),
            State({"type": "snapshot-balance", "account_id": dash.ALL}, "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def save_snapshots(n_clicks, period_id, account_ids, balances, session_data):
        """Save balance snapshots."""
        if not n_clicks or not period_id:
            raise PreventUpdate

        if not session_data or "token" not in session_data:
            return "Please log in first", "danger", True

        token = session_data["token"]
        api_client.set_token(token)

        # Prepare snapshots data
        snapshots = []
        for account_dict, balance in zip(account_ids, balances):
            if balance is not None and balance != "":
                snapshots.append({
                    "account_id": account_dict["account_id"],
                    "balance": float(balance)
                })

        if not snapshots:
            return "Please enter at least one balance", "warning", True

        # Save snapshots
        response = api_client.post(f"/periods/{period_id}/snapshots", snapshots)

        if "error" in response:
            error_data = response["error"]
            if isinstance(error_data, list):
                # Format Pydantic errors for readability
                error_msgs = []
                for err in error_data:
                    loc = " -> ".join(str(l) for l in err.get("loc", []))
                    msg = err.get("msg", "Unknown error")
                    error_msgs.append(f"[{loc}]: {msg}")
                return html.Div([
                    html.Strong("Validation Error: "),
                    html.Ul([html.Li(m) for m in error_msgs])
                ]), "danger", True
            return f"Error saving snapshots: {error_data}", "danger", True

        return "Snapshots saved successfully!", "success", True

    @app.callback(
        Output("recon-trigger-store", "data"),
        [Input("save-snapshots-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def trigger_recon_on_snapshot_save(n_clicks):
        if not n_clicks:
             raise dash.exceptions.PreventUpdate
        from datetime import datetime
        return datetime.now().timestamp()

    @app.callback(
        [
            Output("recon-summary-container", "children", allow_duplicate=True),
            Output("recon-balanced-store", "data", allow_duplicate=True),
        ],
        [Input("calculate-recon-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def calculate_reconciliation(n_clicks, period_id, session_data):
        """Calculate and display reconciliation summary."""
        if not n_clicks or not period_id:
            raise PreventUpdate

        if not session_data or "token" not in session_data:
            return dbc.Alert("Please log in first", color="danger"), False

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get(f"/periods/{period_id}/reconciliation")

        if "error" in response:
            return dbc.Alert(f"Error calculating reconciliation: {response['error']}", color="danger"), False

        reconciliations = response.get("reconciliations", [])
        overall_balanced = response.get("overall_balanced", False)

        if not reconciliations:
            return dbc.Alert("No reconciliation data available. Please add income, expenses, and snapshots.", color="warning"), False

        period_status = response.get("status", "")
        summary_cards = [
            create_recon_currency_card(s, period_id=period_id, period_status=period_status)
            for s in reconciliations
        ]

        # Overall status banner
        overall_banner = dbc.Alert(
            [
                html.I(className=f"bi bi-{'check-circle' if overall_balanced else 'x-circle'} me-2"),
                html.Strong(
                    "All currencies are balanced! You can finalize this period." if overall_balanced
                    else "Some currencies are not balanced. Please review and adjust before finalizing."
                ),
            ],
            color="success" if overall_balanced else "danger",
            className="mb-4 shadow-sm",
        )

        return html.Div([overall_banner, dbc.Row(summary_cards)]), overall_balanced

    @app.callback(
        Output("finalize-button-container", "children"),
        [Input("recon-balanced-store", "data")],
        [State("current-period-id", "data")],
    )
    def update_finalize_button(is_balanced, period_id):
        """Enable/disable finalize button based on reconciliation status."""
        if not is_balanced or not period_id:
            return dbc.Button(
                "Finalize Period",
                id="open-finalize-modal-btn",
                color="secondary",
                disabled=True,
            )

        return dbc.Button(
            [html.I(className="bi bi-lock-fill me-2"), "Finalize Period"],
            id="open-finalize-modal-btn",
            color="danger",
            size="lg",
        )

    @app.callback(
        Output("finalize-modal", "is_open"),
        [
            Input("open-finalize-modal-btn", "n_clicks"),
            Input("finalize-cancel-btn", "n_clicks"),
            Input("finalize-confirm-btn", "n_clicks"),
        ],
        [State("finalize-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_finalize_modal(open_clicks, cancel_clicks, confirm_clicks, is_open):
        """Toggle finalize confirmation modal based on button clicks."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open
        
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Only toggle if one of the buttons was actually clicked (not just rendered)
        if any(triggered_id == btn_id for btn_id in ["open-finalize-modal-btn", "finalize-cancel-btn", "finalize-confirm-btn"]):
            # Double check n_clicks is not None
            trigger_val = ctx.triggered[0]["value"]
            if trigger_val:
                return not is_open
        
        return is_open

    @app.callback(
        [
            Output("finalize-message", "children"),
            Output("finalize-message", "color"),
            Output("finalize-message", "is_open"),
        ],
        [Input("finalize-confirm-btn", "n_clicks")],
        [
            State("current-period-id", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def finalize_period(n_clicks, period_id, session_data):
        """Finalize the period."""
        if not n_clicks or not period_id:
            raise PreventUpdate

        if not session_data or "token" not in session_data:
            return "Please log in first", "danger", True

        token = session_data["token"]
        api_client.set_token(token)

        # Finalize period
        response = api_client.patch(f"/periods/{period_id}/finalize", {})

        if "error" in response:
            return f"Cannot finalize period: {response['error']}", "danger", True

        return (
            "Period finalized successfully! All transactions are now locked.",
            "success",
            True,
        )

    @app.callback(
        Output("tax-benefits-container", "children"),
        [Input("current-period-id", "data"), Input("session-store", "data")],
        prevent_initial_call=True,
    )
    def load_tax_benefits(period_id, session_data):
        """Load and display tax benefits panel when B2B tax system is active."""
        if not period_id or not session_data or "token" not in session_data:
            return []

        token = session_data["token"]
        api_client.set_token(token)

        response = api_client.get(f"/periods/{period_id}/tax-benefits")

        # 204 / not applicable → hide section
        if not response or "error" in response or response.get("tax_system") == "NONE":
            return []

        tax_system = response.get("tax_system", "")
        tax_rate = response.get("tax_rate", 0)
        taxable_income = float(response.get("taxable_income", 0))
        deductible_expenses = float(response.get("deductible_expenses", 0))
        net_taxable = float(response.get("net_taxable_income", 0))
        estimated_tax = float(response.get("estimated_tax", 0))
        tax_savings = float(response.get("tax_savings", 0))
        deductible_items = response.get("deductible_items", [])

        # Build deductible items table rows
        item_rows = []
        for item in deductible_items:
            item_rows.append(
                html.Tr([
                    html.Td(item.get("item_name", "")),
                    html.Td(f"{float(item.get('amount', 0)):,.2f}", className="text-end"),
                ])
            )

        items_table = html.Div()
        if item_rows:
            items_table = dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("Deductible Expense"), html.Th("Amount", className="text-end")])),
                    html.Tbody(item_rows),
                ],
                bordered=True,
                size="sm",
                className="mt-3",
            )
        else:
            items_table = dbc.Alert("No tax-deductible expenses this period.", color="light", className="mt-3")

        system_label = {"POLISH_B2B": "Polish B2B", "US_ANNUAL": "US Annual"}.get(tax_system, tax_system)

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4([
                        html.I(className="bi bi-calculator me-2"),
                        f"Tax Summary ({system_label} — {tax_rate}%)",
                    ])
                ),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.P("Taxable Income", className="text-muted small mb-1"),
                                    html.H5(f"{taxable_income:,.2f}", className="text-success"),
                                ])
                            ], className="text-center"),
                        ], md=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.P("Deductible Expenses", className="text-muted small mb-1"),
                                    html.H5(f"−{deductible_expenses:,.2f}", className="text-primary"),
                                ])
                            ], className="text-center"),
                        ], md=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.P("Estimated Tax", className="text-muted small mb-1"),
                                    html.H5(f"{estimated_tax:,.2f}", className="text-danger"),
                                ])
                            ], className="text-center"),
                        ], md=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.P("Tax Savings", className="text-muted small mb-1"),
                                    html.H5(f"{tax_savings:,.2f}", className="text-warning"),
                                ])
                            ], className="text-center"),
                        ], md=3),
                    ], className="mb-3"),
                    html.Hr(),
                    html.H6("Deductible Items", className="mb-2"),
                    items_table,
                ]),
            ],
            className="mb-4 shadow-sm border-primary",
        )

    @app.callback(
        [
            Output("quick-balance-alert-container", "children"),
            Output("recon-summary-container", "children", allow_duplicate=True),
            Output("recon-balanced-store", "data", allow_duplicate=True),
        ],
        [Input({"type": "quick-balance-btn", "currency": dash.ALL}, "n_clicks")],
        [
            State({"type": "quick-balance-btn", "currency": dash.ALL}, "id"),
            State("current-period-id", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_quick_balance(n_clicks_list, btn_ids, period_id, session_data):
        """Handle quick-balance button click: auto-create Untracked Expenses entry."""
        if not any(n for n in (n_clicks_list or []) if n):
            raise dash.exceptions.PreventUpdate

        if not period_id or not session_data or "token" not in session_data:
            return dbc.Alert("Not authenticated", color="danger"), dash.no_update, dash.no_update

        token = session_data["token"]
        api_client.set_token(token)

        # Determine which button was clicked
        clicked_currency = None
        for clicks, btn_id in zip(n_clicks_list or [], btn_ids or []):
            if clicks:
                clicked_currency = btn_id["currency"]
                break

        if not clicked_currency:
            raise dash.exceptions.PreventUpdate

        resp = api_client.post(
            f"/periods/{period_id}/quick-balance",
            {"currency_ticker": clicked_currency},
        )

        if "error" in resp:
            alert = dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle me-2"), f"Error: {resp['error']}"],
                color="danger", dismissable=True, className="mb-3",
            )
            return alert, dash.no_update, dash.no_update

        # Reload reconciliation
        recon_resp = api_client.get(f"/periods/{period_id}/reconciliation")
        if "error" in recon_resp:
            alert = dbc.Alert("Expense added. Refresh to see updated reconciliation.", color="success", dismissable=True)
            return alert, dash.no_update, dash.no_update

        reconciliations = recon_resp.get("reconciliations", [])
        overall_balanced = recon_resp.get("overall_balanced", False)
        period_status = recon_resp.get("status", "")
        summary_cards = [
            create_recon_currency_card(s, period_id=period_id, period_status=period_status)
            for s in reconciliations
        ]
        overall_banner = dbc.Alert(
            [
                html.I(className=f"bi bi-{'check-circle' if overall_balanced else 'x-circle'} me-2"),
                html.Strong(
                    "All currencies are balanced! You can finalize this period." if overall_balanced
                    else "Some currencies are not balanced. Please review and adjust before finalizing."
                ),
            ],
            color="success" if overall_balanced else "danger",
            className="mb-4 shadow-sm",
        )
        alert = dbc.Alert(
            [html.I(className="bi bi-check-circle me-2"), f"Added Untracked Expenses for {clicked_currency}."],
            color="success", dismissable=True, className="mb-3",
        )
        return alert, html.Div([overall_banner, dbc.Row(summary_cards)]), overall_balanced
