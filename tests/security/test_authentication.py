from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from typing import Any

import pytest

from .clients.lab_api import LabApiClient, json_object
from .config import SecurityTestSettings
from .fixtures.identities import IdentityCatalog
from .fixtures.state import SeedResources, message_list

pytestmark = pytest.mark.security_integration


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _signed_synthetic_jwt(
    settings: SecurityTestSettings,
    user_id: str,
    *,
    algorithm: str = "HS256",
    payload_updates: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    header = {"alg": algorithm, "typ": "JWT"}
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": "user",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + 300,
    }
    payload.update(payload_updates or {})
    encoded_header = _base64url(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode()
    )
    encoded_payload = _base64url(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    digest = hashlib.sha256 if algorithm == "HS256" else hashlib.sha384
    signature = hmac.new(settings.jwt_secret.encode(), signing_input, digest).digest()
    return f"{encoded_header}.{encoded_payload}.{_base64url(signature)}"


def test_valid_login_returns_bounded_bearer_contract(
    api: LabApiClient,
    identities: IdentityCatalog,
) -> None:
    response = api.login_response(identities.user_a)

    assert response.status_code == 200
    payload = json_object(response)
    assert payload.get("tokenType") == "Bearer"
    assert isinstance(payload.get("accessToken"), str)
    assert isinstance(payload.get("expiresIn"), int)
    assert 60 <= payload["expiresIn"] <= 3_600


def test_login_error_does_not_enumerate_accounts(
    api: LabApiClient,
    identities: IdentityCatalog,
) -> None:
    wrong_known = api.request(
        "POST",
        "/auth/login",
        json={
            "email": identities.user_a.email,
            "password": identities.unknown.password,
        },
    )
    unknown = api.login_response(identities.unknown)

    assert wrong_known.status_code == unknown.status_code == 401
    assert json_object(wrong_known) == json_object(unknown)
    assert json_object(unknown).get("message") == "Invalid email or password"


def test_password_reset_request_does_not_enumerate_accounts(
    api: LabApiClient,
    identities: IdentityCatalog,
) -> None:
    known = api.request(
        "POST",
        "/auth/reset-password",
        json={"email": identities.user_a.email},
    )
    unknown = api.request(
        "POST",
        "/auth/reset-password",
        json={"email": identities.unknown.email},
    )

    assert known.status_code == unknown.status_code == 202
    assert json_object(known) == json_object(unknown)


def test_reset_token_is_opaque_and_single_use(
    api: LabApiClient,
    identities: IdentityCatalog,
    settings: SecurityTestSettings,
) -> None:
    requested = api.request(
        "POST",
        "/auth/reset-password",
        json={"email": identities.user_a.email},
    )
    assert requested.status_code == 202
    messages = message_list(api.mailbox())
    assert len(messages) == 1
    token = messages[0].get("resetToken")
    expires_at = messages[0].get("expiresAt")
    assert isinstance(token, str)
    assert isinstance(expires_at, str)
    assert len(token) >= 43
    assert identities.user_a.email not in token
    expires_in = datetime.fromisoformat(expires_at.replace("Z", "+00:00")) - datetime.now(UTC)
    assert 0 < expires_in.total_seconds() <= 3_600

    first_use = api.request(
        "POST",
        "/auth/reset-password/confirm",
        json={"token": token, "newPassword": settings.replacement_password},
    )
    replay = api.request(
        "POST",
        "/auth/reset-password/confirm",
        json={"token": token, "newPassword": settings.replacement_password},
    )

    assert first_use.status_code == 200
    assert replay.status_code == 401
    assert json_object(replay).get("message") == "Invalid or expired reset token"
    changed_password = api.request(
        "POST",
        "/auth/login",
        json={
            "email": identities.user_a.email,
            "password": settings.replacement_password,
        },
    )
    old_password = api.login_response(identities.user_a)
    assert changed_password.status_code == 200
    assert old_password.status_code == 401


def test_protected_resource_rejects_missing_and_tampered_bearer_tokens(
    api: LabApiClient,
    identities: IdentityCatalog,
    resources: SeedResources,
) -> None:
    property_id = resources.user_a.property_id
    assert property_id is not None
    missing = api.request("GET", f"/properties/{property_id}")

    valid_token = api.login(identities.user_a)
    token_parts = valid_token.split(".")
    assert len(token_parts) == 3 and token_parts[2]
    first_signature_character = "A" if token_parts[2][0] != "A" else "B"
    token_parts[2] = first_signature_character + token_parts[2][1:]
    tampered_token = ".".join(token_parts)
    tampered = api.request(
        "GET",
        f"/properties/{property_id}",
        token=tampered_token,
    )

    assert missing.status_code == tampered.status_code == 401
    assert json_object(missing).get("message") == "Unauthorized"
    assert json_object(tampered).get("message") == "Unauthorized"


def test_synthetic_jwt_settings_match_the_running_lab(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    property_id = resources.user_a.property_id
    assert property_id is not None
    token = _signed_synthetic_jwt(settings, resources.user_a.user_id)

    response = api.request("GET", f"/properties/{property_id}", token=token)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "invalid_claims_case",
    ["wrong-issuer", "wrong-audience", "expired", "non-allowlisted-algorithm"],
)
def test_jwt_validation_rejects_invalid_claims_and_algorithms(
    invalid_claims_case: str,
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    now = int(time.time())
    payload_updates: dict[str, Any] = {}
    algorithm = "HS256"
    if invalid_claims_case == "wrong-issuer":
        payload_updates["iss"] = f"{settings.jwt_issuer}-wrong"
    elif invalid_claims_case == "wrong-audience":
        payload_updates["aud"] = f"{settings.jwt_audience}-wrong"
    elif invalid_claims_case == "expired":
        payload_updates.update({"iat": now - 600, "exp": now - 300})
    elif invalid_claims_case == "non-allowlisted-algorithm":
        algorithm = "HS384"
    else:
        raise AssertionError(f"Unknown JWT test case {invalid_claims_case}")

    token = _signed_synthetic_jwt(
        settings,
        resources.user_a.user_id,
        algorithm=algorithm,
        payload_updates=payload_updates,
    )
    property_id = resources.user_a.property_id
    assert property_id is not None

    response = api.request("GET", f"/properties/{property_id}", token=token)

    assert response.status_code == 401
    assert json_object(response).get("message") == "Unauthorized"


def test_authentication_requires_json_content_type(
    api: LabApiClient,
    identities: IdentityCatalog,
) -> None:
    response = api.request(
        "POST",
        "/auth/login",
        content=f"email={identities.user_a.email}",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 415


def test_password_policy_rejection_does_not_consume_reset_token(
    api: LabApiClient,
    identities: IdentityCatalog,
    settings: SecurityTestSettings,
) -> None:
    requested = api.request(
        "POST",
        "/auth/reset-password",
        json={"email": identities.user_a.email},
    )
    assert requested.status_code == 202
    messages = message_list(api.mailbox())
    assert len(messages) == 1
    token = messages[0].get("resetToken")
    assert isinstance(token, str)

    weak = api.request(
        "POST",
        "/auth/reset-password/confirm",
        json={"token": token, "newPassword": settings.replacement_password.lower()},
    )
    strong = api.request(
        "POST",
        "/auth/reset-password/confirm",
        json={"token": token, "newPassword": settings.replacement_password},
    )

    assert weak.status_code == 400
    assert strong.status_code == 200
