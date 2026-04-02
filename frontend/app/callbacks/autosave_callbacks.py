"""Auto-save draft callbacks for income and expense forms.

Drafts are persisted to session-scoped dcc.Store components so that
switching tabs doesn't lose unsaved form data. The indicator shows a
subtle "Draft saved" message whenever the form changes.
"""
from datetime import datetime

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate


def register_autosave_callbacks(app):
    """Register auto-save draft callbacks for income and expense forms."""

    # ------------------------------------------------------------------
    # Income draft auto-save
    # ------------------------------------------------------------------
    @app.callback(
        Output("income-draft-store", "data"),
        Output("income-autosave-indicator", "children"),
        Input("income-source-name", "value"),
        Input("income-amount", "value"),
        Input("income-currency", "value"),
        Input("income-date", "value"),
        Input("income-notes", "value"),
        prevent_initial_call=True,
    )
    def save_income_draft(source_name, amount, currency_id, income_date, notes):
        # Only save if at least one meaningful field has content
        if not any([source_name, amount]):
            return no_update, no_update

        draft = {
            "source_name": source_name,
            "amount": amount,
            "currency_id": currency_id,
            "income_date": income_date,
            "notes": notes,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        ts = datetime.now().strftime("%H:%M:%S")
        return draft, f"Draft saved at {ts}"

    @app.callback(
        Output("income-source-name", "value"),
        Output("income-amount", "value"),
        Output("income-notes", "value"),
        Input("income-draft-store", "data"),
        State("income-source-name", "value"),
        prevent_initial_call=True,
    )
    def restore_income_draft(draft, current_name):
        """Restore draft when the tab loads and the form is empty."""
        if not draft or current_name:
            raise PreventUpdate
        return (
            draft.get("source_name") or no_update,
            draft.get("amount") or no_update,
            draft.get("notes") or no_update,
        )

    # ------------------------------------------------------------------
    # Expense draft auto-save
    # ------------------------------------------------------------------
    @app.callback(
        Output("expense-draft-store", "data"),
        Output("expense-autosave-indicator", "children"),
        Input("expense-item-name", "value"),
        Input("expense-amount", "value"),
        Input("expense-category", "value"),
        Input("expense-currency", "value"),
        Input("expense-date", "value"),
        Input("expense-notes", "value"),
        prevent_initial_call=True,
    )
    def save_expense_draft(item_name, amount, category_id, currency_id, expense_date, notes):
        if not any([item_name, amount]):
            return no_update, no_update

        draft = {
            "item_name": item_name,
            "amount": amount,
            "category_id": category_id,
            "currency_id": currency_id,
            "expense_date": expense_date,
            "notes": notes,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        ts = datetime.now().strftime("%H:%M:%S")
        return draft, f"Draft saved at {ts}"

    @app.callback(
        Output("expense-item-name", "value"),
        Output("expense-amount", "value"),
        Output("expense-notes", "value"),
        Input("expense-draft-store", "data"),
        State("expense-item-name", "value"),
        prevent_initial_call=True,
    )
    def restore_expense_draft(draft, current_name):
        """Restore draft when the tab loads and the form is empty."""
        if not draft or current_name:
            raise PreventUpdate
        return (
            draft.get("item_name") or no_update,
            draft.get("amount") or no_update,
            draft.get("notes") or no_update,
        )
