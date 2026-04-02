import requests
from typing import Optional, Dict, Any


class APIClient:
    """Client for interacting with the BudgetFlow backend API."""

    def __init__(self, base_url: str = "http://backend:8000/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def set_token(self, token: str) -> None:
        """Set the authentication token."""
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if token exists."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 401:
                return {"error": "AUTHENTICATION_ERROR", "detail": "Session expired or invalid credentials"}
            response.raise_for_status()
            if response.status_code == 204 or not response.text:
                return {}
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_error(e)

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            if response.status_code == 401:
                return {"error": "AUTHENTICATION_ERROR", "detail": "Session expired or invalid credentials"}
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_error(e)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.put(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            if response.status_code == 401:
                return {"error": "AUTHENTICATION_ERROR", "detail": "Session expired or invalid credentials"}
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_error(e)

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PATCH request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.patch(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            if response.status_code == 401:
                return {"error": "AUTHENTICATION_ERROR", "detail": "Session expired or invalid credentials"}
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._handle_error(e)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.delete(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 401:
                return {"error": "AUTHENTICATION_ERROR", "detail": "Session expired or invalid credentials"}
            response.raise_for_status()
            return response.json() if response.text else {"success": True}
        except requests.exceptions.RequestException as e:
            return self._handle_error(e)

    def _handle_error(self, e: requests.exceptions.RequestException) -> Dict[str, Any]:
        """Centralized error handling for requests."""
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_json = e.response.json()
                if "detail" in error_json:
                    return {"error": error_json["detail"]}
            except Exception:
                pass
        return {"error": str(e)}
