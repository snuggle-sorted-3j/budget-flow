"""Onboarding wizard callbacks for BudgetFlow first-time setup."""
import json

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate

from components.onboarding_wizard import ONBOARDING_STEPS, TOTAL_STEPS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _triggered_id() -> str | None:
    ctx = callback_context
    if not ctx.triggered:
        return None
    return ctx.triggered[0]["prop_id"].split(".")[0]


def _dots(current_step: int) -> list:
    """Render progress dot divs."""
    dots = []
    for s in ONBOARDING_STEPS:
        if s["num"] < current_step:
            cls = "onboarding-dot done"
        elif s["num"] == current_step:
            cls = "onboarding-dot active"
        else:
            cls = "onboarding-dot"
        dots.append(html.Div(className=cls))
    return dots


def _panel_body(step: dict, on_correct_page: bool) -> list:
    """Build the body content for a given step."""
    if not on_correct_page:
        return [
            html.P(step["description"], className="description"),
            html.Div(
                [
                    html.I(className="bi bi-arrow-right-circle-fill me-2"),
                    html.Span(
                        f"Navigate to the {step['title']} page using the sidebar — "
                        "the guide will continue automatically."
                    ),
                ],
                className="onboarding-navigate-hint",
            ),
            dbc.Button(
                [html.I(className="bi bi-arrow-right me-1"), f" {step['nav_label']}"],
                href=step["path"],
                color="primary",
                size="sm",
                className="w-100",
            ),
        ]
    return [
        html.P(step["description"], className="description"),
        html.Div(
            [
                html.I(className="bi bi-pencil-square me-2"),
                html.Span(step["instruction"]),
            ],
            className="instruction-box d-flex align-items-start",
        ),
        html.Small(
            [
                html.I(className="bi bi-arrow-up me-1"),
                "The highlighted fields above show what to fill in",
            ],
            className="text-muted d-block mt-1",
            style={"fontSize": "0.78rem"},
        ),
    ]


# ---------------------------------------------------------------------------
# Public registration function
# ---------------------------------------------------------------------------

def register_onboarding_callbacks(app) -> None:
    """Register all onboarding wizard callbacks on the Dash app."""

    # ------------------------------------------------------------------
    # 1. Welcome modal open/close
    # ------------------------------------------------------------------
    @app.callback(
        Output("onboarding-welcome-modal", "is_open"),
        [
            Input("onboarding-state", "data"),
            Input("url", "pathname"),
            Input("onboarding-start-btn", "n_clicks"),
            Input("onboarding-skip-all-btn", "n_clicks"),
        ],
        prevent_initial_call=False,
    )
    def control_welcome_modal(state, pathname, _start, _skip_all):
        triggered = _triggered_id()

        if triggered in ("onboarding-start-btn", "onboarding-skip-all-btn"):
            return False

        if not pathname or not pathname.startswith("/dashboard"):
            return False

        if not state:
            return False

        # Show only when tour hasn't been started yet (step == 0, not completed)
        return not state.get("completed", False) and state.get("step", 0) == 0

    # ------------------------------------------------------------------
    # 2. State machine — advance / skip / finish / dismiss / restart
    # ------------------------------------------------------------------
    @app.callback(
        Output("onboarding-state", "data"),
        [
            Input("onboarding-start-btn", "n_clicks"),
            Input("onboarding-skip-all-btn", "n_clicks"),
            Input("onboarding-next-btn", "n_clicks"),
            Input("onboarding-skip-btn", "n_clicks"),
            Input("onboarding-finish-btn", "n_clicks"),
            Input("onboarding-dismiss-btn", "n_clicks"),
            Input("onboarding-restart-btn", "n_clicks"),
        ],
        State("onboarding-state", "data"),
        prevent_initial_call=True,
    )
    def update_onboarding_state(
        _start, _skip_all, _next, _skip, _finish, _dismiss, _restart, state
    ):
        triggered = _triggered_id()
        if triggered is None:
            raise PreventUpdate

        if state is None:
            state = {"completed": False, "step": 0}

        step = state.get("step", 0)

        if triggered == "onboarding-start-btn":
            return {"completed": False, "step": 1}

        if triggered in ("onboarding-skip-all-btn", "onboarding-dismiss-btn"):
            return {"completed": True, "step": step}

        if triggered == "onboarding-restart-btn":
            return {"completed": False, "step": 1}

        if triggered in ("onboarding-next-btn", "onboarding-skip-btn"):
            next_step = step + 1
            if next_step > TOTAL_STEPS:
                return {"completed": True, "step": 0}
            return {"completed": False, "step": next_step}

        if triggered == "onboarding-finish-btn":
            return {"completed": True, "step": 0}

        raise PreventUpdate

    # ------------------------------------------------------------------
    # 3. Update panel content + visibility (no component re-creation)
    # ------------------------------------------------------------------
    @app.callback(
        [
            Output("onboarding-panel", "style"),
            Output("onboarding-backdrop", "className"),
            Output("onboarding-step-badge", "children"),
            Output("onboarding-panel-title", "children"),
            Output("onboarding-panel-subtitle", "children"),
            Output("onboarding-panel-body", "children"),
            Output("onboarding-dots-container", "children"),
            Output("onboarding-skip-btn", "style"),
            Output("onboarding-next-btn", "style"),
            Output("onboarding-finish-btn", "style"),
        ],
        [
            Input("onboarding-state", "data"),
            Input("url", "pathname"),
        ],
    )
    def update_wizard_panel(state, pathname):
        hidden_panel = {"display": "none"}
        backdrop_hidden = "d-none"
        empty = [None] * 8  # remaining outputs when hidden

        if not state or state.get("completed", False):
            return hidden_panel, backdrop_hidden, *empty

        step_num = state.get("step", 0)
        if step_num < 1 or step_num > TOTAL_STEPS:
            return hidden_panel, backdrop_hidden, *empty

        step = next(s for s in ONBOARDING_STEPS if s["num"] == step_num)
        on_correct_page = pathname == step["path"]
        is_last = step_num == TOTAL_STEPS
        is_optional = not step["required"]

        badge_text = f"Step {step_num} of {TOTAL_STEPS}"
        dots = _dots(step_num)
        body = _panel_body(step, on_correct_page)

        # Button visibility
        skip_style = {} if is_optional else {"display": "none"}
        next_style = {"display": "none"} if is_last else {}
        finish_style = {} if is_last else {"display": "none"}

        return (
            {"display": "block"},       # panel visible
            "onboarding-backdrop",      # backdrop visible
            badge_text,
            step["title"],
            step["subtitle"],
            body,
            dots,
            skip_style,
            next_style,
            finish_style,
        )

    # ------------------------------------------------------------------
    # 4. Clientside: apply/remove onboarding-highlight CSS class on fields
    # ------------------------------------------------------------------
    _step_field_map = {str(s["num"]): s["highlight_ids"] for s in ONBOARDING_STEPS}
    _step_path_map = {str(s["num"]): s["path"] for s in ONBOARDING_STEPS}

    app.clientside_callback(
        f"""
        function(state, pathname) {{
            var stepMap  = {json.dumps(_step_field_map)};
            var pathMap  = {json.dumps(_step_path_map)};

            // Always clear previous highlights
            document.querySelectorAll('.onboarding-highlight').forEach(function(el) {{
                el.classList.remove('onboarding-highlight');
            }});

            if (!state || state.completed) return null;

            var step = String(state.step);
            if (!step || step === '0') return null;

            if (pathname !== pathMap[step]) return null;

            var ids = stepMap[step];
            if (!ids) return null;

            setTimeout(function() {{
                ids.forEach(function(id, idx) {{
                    var el = document.getElementById(id);
                    if (el) {{
                        el.classList.add('onboarding-highlight');
                        if (idx === 0) {{
                            el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        }}
                    }}
                }});
            }}, 350);

            return null;
        }}
        """,
        Output("onboarding-highlight-dummy", "data"),
        [
            Input("onboarding-state", "data"),
            Input("url", "pathname"),
        ],
    )
