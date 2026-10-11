from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import httpx

from ..config import SecurityTestSettings
from ..fixtures.identities import Credentials

type JsonObject = dict[str, Any]


def json_object(response: httpx.Response) -> JsonObject:
    value: object = response.json()
    if not isinstance(value, dict):
        raise AssertionError(f"Expected a JSON object, received {type(value).__name__}")
    return cast(JsonObject, value)


class LabApiClient:
    """Small contract client that cannot follow redirects or target another host."""

    def __init__(self, settings: SecurityTestSettings) -> None:
        self._test_key = settings.lab_test_key
        self._client = httpx.Client(
            base_url=settings.normalized_base_url,
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            follow_redirects=False,
            headers={"Accept": "application/json"},
        )

    def __enter__(self) -> LabApiClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        if not path.startswith("/") or path.startswith("//") or "://" in path:
            raise ValueError("LabApiClient accepts only absolute-path references")
        request_headers = dict(headers or {})
        if token is not None:
            request_headers["Authorization"] = f"Bearer {token}"
        response = self._client.request(
            method,
            path,
            headers=request_headers,
            **kwargs,
        )
        if response.history:
            raise AssertionError("Security test client unexpectedly followed a redirect")
        return response

    def login_response(self, credentials: Credentials) -> httpx.Response:
        return self.request(
            "POST",
            "/auth/login",
            json={"email": credentials.email, "password": credentials.password},
        )

    def login(self, credentials: Credentials) -> str:
        response = self.login_response(credentials)
        if response.status_code != 200:
            raise AssertionError(
                f"Synthetic identity {credentials.actor.value} could not log in: "
                f"HTTP {response.status_code}"
            )
        payload = json_object(response)
        token = payload.get("accessToken")
        if not isinstance(token, str) or not token:
            raise AssertionError("Login response did not contain a non-empty accessToken")
        return token

    def reset(self) -> None:
        response = self.request(
            "POST",
            "/__test/reset",
            headers={"X-Lab-Test-Key": self._test_key},
        )
        if response.status_code != 204 or response.content:
            raise AssertionError(
                f"Lab reset contract failed: HTTP {response.status_code}, body={response.text!r}"
            )
        self._client.cookies.clear()

    def state(self) -> JsonObject:
        response = self.request(
            "GET",
            "/__test/state",
            headers={"X-Lab-Test-Key": self._test_key},
        )
        if response.status_code != 200:
            raise AssertionError(f"Lab state endpoint returned HTTP {response.status_code}")
        return json_object(response)

    def mailbox(self) -> JsonObject:
        response = self.request(
            "GET",
            "/__test/mailbox",
            headers={"X-Lab-Test-Key": self._test_key},
        )
        if response.status_code != 200:
            raise AssertionError(f"Lab mailbox endpoint returned HTTP {response.status_code}")
        return json_object(response)

    def logs(self) -> JsonObject:
        response = self.request(
            "GET",
            "/__test/logs",
            headers={"X-Lab-Test-Key": self._test_key},
        )
        if response.status_code != 200:
            raise AssertionError(f"Lab logs endpoint returned HTTP {response.status_code}")
        return json_object(response)
