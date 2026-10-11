from __future__ import annotations

import json
import time

import pytest

from .clients.lab_api import LabApiClient
from .config import SecurityTestSettings
from .fixtures.identities import IdentityCatalog
from .fixtures.state import message_list

pytestmark = pytest.mark.security_integration


def test_structured_security_logs_exclude_credentials_tokens_prompts_and_pii(
    api: LabApiClient,
    identities: IdentityCatalog,
    settings: SecurityTestSettings,
) -> None:
    password_sentinel = "Log-Sentinel-Password!42"
    prompt_sentinel = "LOG_SENTINEL_PROMPT_CONTENT"
    invalid_signature_sentinel = "a" * 64

    failed_login = api.request(
        "POST",
        "/auth/login",
        json={"email": identities.user_a.email, "password": password_sentinel},
    )
    assert failed_login.status_code == 401

    reset = api.request(
        "POST",
        "/auth/reset-password",
        json={"email": identities.user_a.email},
    )
    assert reset.status_code == 202
    messages = message_list(api.mailbox())
    assert len(messages) == 1
    reset_token = messages[0].get("resetToken")
    assert isinstance(reset_token, str)

    access_token = api.login(identities.user_a)
    ai_response = api.request(
        "POST",
        "/ai/parse",
        token=access_token,
        json={"text": prompt_sentinel},
    )
    assert ai_response.status_code == 201

    now = int(time.time())
    invalid_webhook = api.request(
        "POST",
        "/webhooks/stripe",
        content=b'{"id":"evt_log_redaction","type":"synthetic","created":1}',
        headers={
            "Content-Type": "application/json",
            "stripe-signature": f"t={now},v1={invalid_signature_sentinel}",
        },
    )
    assert invalid_webhook.status_code == 401

    serialized_logs = json.dumps(api.logs(), sort_keys=True)
    for forbidden in (
        identities.user_a.email,
        password_sentinel,
        reset_token,
        access_token,
        prompt_sentinel,
        invalid_signature_sentinel,
        settings.webhook_secret,
    ):
        assert forbidden not in serialized_logs
