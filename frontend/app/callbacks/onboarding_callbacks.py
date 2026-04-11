"""Onboarding wizard callbacks for BudgetFlow first-time setup."""
import json

from dash import Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate

from components.onboarding_wizard import (
    ONBOARDING_STEPS,
    TOTAL_STEPS,
    create_step_panel,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _triggered_id() -> str | None:
    ctx = callback_context
    if not ctx.triggered:
        return None
    return ctx.triggered[0]["prop_id"].split(".")[0]


# ---------------------------------------------------------------------------
# Public registration function
# ---------------------------------------------------------------------------

def register_onboarding_callbacks(app) -> None:
    """Register all onboarding wizard callbacks on the Dash app."""

    # ------------------------------------------------------------------
    # 1. Show welcome modal when a new user first lands on the dashboard
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
    def control_welcome_modal(state, pathname, start_clicks, skip_all_clicks):
        triggered = _triggered_id()

        # Close if user clicked Start or Skip All
        if triggered in ("onboarding-start-btn", "onboarding-skip-all-btn"):
            return False

        # Only show on dashboard pages
        if not pathname or not pathname.startswith("/dashboard"):
            return False

        if state is None:
            return False

        # Show only when not completed and step == 0 (never started)
        if not state.get("completed", False) and state.get("step", 0) == 0:
            return True

        return False

    # ------------------------------------------------------------------
    # 2. State machine — advance, skip, finish, dismiss, or restart
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
        start, skip_all, next_click, skip, finish, dismiss, restart, state
    ):
        triggered = _triggered_id()
        if triggered is None:
            raise PreventUpdate

        if state is None:
            state = {"completed": False, "step": 0}

        current_step = state.get("step", 0)

        if triggered == "onboarding-start-btn":
            # Begin tour at step 1
            return {"completed": False, "step": 1}

        if triggered == "onboarding-skip-all-btn":
            # User wants to skip everything
            return {"completed": True, "step": 0}

        if triggered == "onboarding-dismiss-btn":
            # Dismiss mid-tour → mark completed so it won't re-appear
            return {"completed": True, "step": current_step}

        if triggered == "onboarding-restart-btn":
            # Re-launch tour from step 1
            return {"completed": False, "step": 1}

        if triggered in ("onboarding-next-btn", "onboarding-skip-btn"):
            next_step = current_step + 1
            if next_step > TOTAL_STEPS:
                return {"completed": True, "step": 0}
            return {"completed": False, "step": next_step}

        if triggered == "onboarding-finish-btn":
            return {"completed": True, "step": 0}

        raise PreventUpdate

    # ------------------------------------------------------------------
    # 3. Render the floating step panel + toggle backdrop
    # ------------------------------------------------------------------
    @app.callback(
        [
            Output("onboarding-panel-container", "children"),
            Output("onboarding-backdrop", "className"),
        ],
        [
            Input("onboarding-state", "data"),
            Input("url", "pathname"),
        ],
    )
    def render_wizard_panel(state, pathname):
        if state is None or state.get("completed", False):
            return None, "d-none"

        step = state.get("step", 0)
        if step < 1 or step > TOTAL_STEPS:
            return None, "d-none"

        panel = create_step_panel(step, pathname or "")
        return panel, "onboarding-backdrop"

    # ------------------------------------------------------------------
    # 4. Clientside callback — apply/remove highlight class on DOM nodes
    # ------------------------------------------------------------------
    # Build a JS map from step number → list of element IDs to highlight
    _step_field_map = {
        str(s["num"]): s["highlight_ids"] for s in ONBOARDING_STEPS
    }
    _step_field_map_json = json.dumps(_step_field_map)

    app.clientside_callback(
        f"""
        function(state, pathname) {{
            var stepMap = {_step_field_map_json};

            // Always clear existing highlights first
            document.querySelectorAll('.onboarding-highlight').forEach(function(el) {{
                el.classList.remove('onboarding-highlight');
            }});

            if (!state || state.completed) {{
                return null;
            }}

            var step = state.step;
            if (!step || step < 1) {{
                return null;
            }}

            var ids = stepMap[String(step)];
            if (!ids) return null;

            // Find the expected path for this step
            var stepPaths = {json.dumps({str(s["num"]): s["path"] for s in ONBOARDING_STEPS})};
            var expectedPath = stepPaths[String(step)];
            if (pathname !== expectedPath) {{
                return null;  // Wrong page — no highlights
            }}

            // Apply highlights after a small delay to let Dash finish rendering
            setTimeout(function() {{
                ids.forEach(function(id) {{
                    var el = document.getElementById(id);
                    if (el) {{
                        el.classList.add('onboarding-highlight');
                        // Scroll the first highlighted element into view
                        if (el === document.getElementById(ids[0])) {{
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
