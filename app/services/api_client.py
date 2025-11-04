from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests


class ApiClient:
    """Cliente HTTP sencillo para consumir la API REST del servidor."""

    def __init__(self, base_url: str, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._token: Optional[str] = None

    def set_token(self, token: Optional[str]) -> None:
        self._token = token

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        payload = json.dumps(data) if data is not None else None
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=self._build_headers(),
            params=params,
            data=payload,
            timeout=self.timeout
        )
        self._raise_for_status(response)
        if response.content:
            return response.json()
        return None

    def _raise_for_status(self, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            message: str
            try:
                message = response.json().get("message", str(error))
            except ValueError:
                message = str(error)
            raise ApiError(status_code=response.status_code, message=message) from error

    # Métodos auxiliares de alto nivel
    def login(self, username: str, password: str) -> Dict[str, Any]:
        result = self.request("POST", "/auth/login", data={"username": username, "password": password})
        self.set_token(result.get("token"))
        return result

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, data: Dict[str, Any]) -> Any:
        return self.request("POST", path, data=data)

    def put(self, path: str, data: Dict[str, Any]) -> Any:
        return self.request("PUT", path, data=data)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)


class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.status_code}] {self.message}"
