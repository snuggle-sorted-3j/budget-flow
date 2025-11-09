import dash
import dash_bootstrap_components as dbc
from dash import html

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="BudgetFlow",
)
server = app.server


def create_layout() -> html.Div:
    """Return the default Dash layout."""

    return html.Div(
        children=[
            html.Header(
                html.H1("BudgetFlow"),
                style={"padding": "1rem", "backgroundColor": "#f8f9fa"},
            ),
            html.Main(
                html.P("Frontend scaffolding is ready.", style={"padding": "1rem"}),
            ),
        ]
    )


app.layout = create_layout()


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)

