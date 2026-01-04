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
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PATCH request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.patch(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.delete(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json() if response.text else {"success": True}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
