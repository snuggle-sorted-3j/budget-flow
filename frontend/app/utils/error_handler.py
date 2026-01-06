"""Error handling utilities for the application."""
import dash_bootstrap_components as dbc
from dash import html


def parse_api_error(response):
    """
    Extract meaningful error message from API response.
    
    Args:
        response: API response (dict or str)
        
    Returns:
        str: Human-readable error message
    """
    if isinstance(response, dict):
        # Check for common error formats
        if "detail" in response:
            detail = response["detail"]
            if isinstance(detail, str):
                return detail
            elif isinstance(detail, list) and len(detail) > 0:
                # Pydantic validation errors
                errors = []
                for err in detail:
                    field = err.get("loc", ["unknown"])[-1]
                    msg = err.get("msg", "Invalid value")
                    errors.append(f"{field}: {msg}")
                return "; ".join(errors)
        
        if "error" in response:
            return str(response["error"])
        
        if "message" in response:
            return str(response["message"])
    
    if isinstance(response, str):
        return response
    
    return "An unexpected error occurred. Please try again."


def display_error(error_response, dismissable=True):
    """
    Create a styled error alert component.
    
    Args:
        error_response: Error message or API response
        dismissable: Whether the alert can be dismissed
        
    Returns:
        dbc.Alert: Styled error alert
    """
    error_msg = parse_api_error(error_response)
    
    return dbc.Alert(
        [
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            error_msg
        ],
        color="danger",
        dismissable=dismissable,
        className="d-flex align-items-center"
    )


def display_success(message, dismissable=True):
    """
    Create a styled success alert component.
    
    Args:
        message: Success message
        dismissable: Whether the alert can be dismissed
        
    Returns:
        dbc.Alert: Styled success alert
    """
    return dbc.Alert(
        [
            html.I(className="bi bi-check-circle-fill me-2"),
            message
        ],
        color="success",
        dismissable=dismissable,
        className="d-flex align-items-center",
        duration=3000  # Auto-dismiss after 3 seconds
    )


def display_warning(message, dismissable=True):
    """
    Create a styled warning alert component.
    
    Args:
        message: Warning message
        dismissable: Whether the alert can be dismissed
        
    Returns:
        dbc.Alert: Styled warning alert
    """
    return dbc.Alert(
        [
            html.I(className="bi bi-exclamation-circle-fill me-2"),
            message
        ],
        color="warning",
        dismissable=dismissable,
        className="d-flex align-items-center"
    )


def display_info(message, dismissable=True):
    """
    Create a styled info alert component.
    
    Args:
        message: Info message
        dismissable: Whether the alert can be dismissed
        
    Returns:
        dbc.Alert: Styled info alert
    """
    return dbc.Alert(
        [
            html.I(className="bi bi-info-circle-fill me-2"),
            message
        ],
        color="info",
        dismissable=dismissable,
        className="d-flex align-items-center"
    )


def create_loading_spinner(text="Loading..."):
    """
    Create a loading spinner with text.
    
    Args:
        text: Loading message
        
    Returns:
        html.Div: Loading spinner component
    """
    return html.Div(
        [
            dbc.Spinner(
                size="lg",
                color="primary",
                spinner_style={"width": "3rem", "height": "3rem"}
            ),
            html.P(text, className="text-muted mt-3 mb-0")
        ],
        className="text-center py-5"
    )


def create_confirmation_modal(modal_id, title, message, confirm_button_text="Confirm", cancel_button_text="Cancel"):
    """
    Create a confirmation modal for destructive actions.
    
    Args:
        modal_id: Unique ID for the modal
        title: Modal title
        message: Confirmation message
        confirm_button_text: Text for confirm button
        cancel_button_text: Text for cancel button
        
    Returns:
        dbc.Modal: Confirmation modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill text-warning me-2"),
                        title
                    ]
                )
            ),
            dbc.ModalBody(
                [
                    html.P(message),
                    html.P(
                        [
                            html.I(className="bi bi-info-circle me-2"),
                            html.Strong("This action cannot be undone.")
                        ],
                        className="text-danger mb-0"
                    )
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        cancel_button_text,
                        id=f"{modal_id}-cancel",
                        className="me-2",
                        color="secondary"
                    ),
                    dbc.Button(
                        confirm_button_text,
                        id=f"{modal_id}-confirm",
                        color="danger"
                    )
                ]
            )
        ],
        id=modal_id,
        is_open=False,
        centered=True
    )


def validate_required_fields(**fields):
    """
    Validate that required fields are not empty.
    
    Args:
        **fields: Field name and value pairs
        
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    for field_name, value in fields.items():
        if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
            errors[field_name] = "This field is required"
    
    return len(errors) == 0, errors


def validate_positive_number(value, field_name="Value"):
    """
    Validate that a value is a positive number.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        num = float(value)
        if num <= 0:
            return False, f"{field_name} must be greater than 0"
        return True, None
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number"


def validate_date(date_str, allow_future=True, field_name="Date"):
    """
    Validate a date string.
    
    Args:
        date_str: Date string to validate
        allow_future: Whether to allow future dates
        field_name: Name of the field for error message
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    from datetime import datetime
    
    if not date_str:
        return False, f"{field_name} is required"
    
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        if not allow_future and date_obj > datetime.now():
            return False, f"{field_name} cannot be in the future"
        
        return True, None
    except ValueError:
        return False, f"{field_name} must be a valid date"
