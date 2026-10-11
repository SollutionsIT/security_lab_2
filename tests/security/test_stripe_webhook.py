from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from uuid import uuid4

import httpx
import pytest

from .clients.lab_api import LabApiClient, json_object
from .config import SecurityTestSettings
from .fixtures.state import (
    SeedResources,
    invoice_from_state,
    webhook_events_from_state,
)

pytestmark = pytest.mark.security_integration


def _raw_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _signature(secret: str, timestamp: int, raw_body: bytes) -> str:
    signed = str(timestamp).encode("ascii") + b"." + raw_body
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def _invoice_paid_event(
    api: LabApiClient,
    resources: SeedResources,
    *,
    timestamp: int,
) -> dict[str, Any]:
    invoice_id = resources.user_a.invoice_id
    assert invoice_id is not None
    invoice = invoice_from_state(api.state(), invoice_id)
    assert invoice is not None
    return {
        "id": f"evt_{uuid4().hex}",
        "type": "invoice.paid",
        "created": timestamp,
        "data": {
            "object": {
                "invoiceId": invoice_id,
                "orderId": invoice.get("orderId"),
                "amountCents": invoice.get("amountCents"),
                "currency": invoice.get("currency"),
            }
        },
    }


def _post_webhook(
    api: LabApiClient,
    raw_body: bytes,
    signature: str | None,
) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["stripe-signature"] = signature
    return api.request(
        "POST",
        "/webhooks/stripe",
        content=raw_body,
        headers=headers,
    )


def _assert_open_invoice_and_no_claimed_event(
    api: LabApiClient,
    resources: SeedResources,
) -> None:
    invoice_id = resources.user_a.invoice_id
    assert invoice_id is not None
    invoice = invoice_from_state(api.state(), invoice_id)
    assert invoice is not None
    assert invoice.get("state") == "open"
    assert webhook_events_from_state(api.state()) == []


def test_missing_signature_is_rejected_without_side_effects(
    api: LabApiClient,
    resources: SeedResources,
) -> None:
    now = int(time.time())
    raw_body = _raw_json(_invoice_paid_event(api, resources, timestamp=now))

    response = _post_webhook(api, raw_body, None)

    assert response.status_code == 401
    _assert_open_invoice_and_no_claimed_event(api, resources)


def test_invalid_signature_is_rejected_without_side_effects(
    api: LabApiClient,
    resources: SeedResources,
) -> None:
    now = int(time.time())
    raw_body = _raw_json(_invoice_paid_event(api, resources, timestamp=now))

    response = _post_webhook(api, raw_body, f"t={now},v1={'0' * 64}")

    assert response.status_code == 401
    _assert_open_invoice_and_no_claimed_event(api, resources)


def test_valid_signature_processes_bound_invoice_once(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    now = int(time.time())
    event = _invoice_paid_event(api, resources, timestamp=now)
    raw_body = _raw_json(event)

    response = _post_webhook(
        api,
        raw_body,
        _signature(settings.webhook_secret, now, raw_body),
    )

    assert response.status_code == 200
    assert json_object(response) == {
        "status": "processed",
        "eventId": event["id"],
        "invoiceId": resources.user_a.invoice_id,
        "invoiceState": "paid",
    }
    state = api.state()
    invoice_id = resources.user_a.invoice_id
    assert invoice_id is not None
    paid_invoice = invoice_from_state(state, invoice_id)
    assert paid_invoice is not None
    assert paid_invoice.get("state") == "paid"
    events = webhook_events_from_state(state)
    assert len(events) == 1
    assert events[0].get("id") == event["id"]
    assert events[0].get("status") == "processed"


def test_duplicate_event_is_idempotent(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    now = int(time.time())
    event = _invoice_paid_event(api, resources, timestamp=now)
    raw_body = _raw_json(event)
    signature = _signature(settings.webhook_secret, now, raw_body)

    first = _post_webhook(api, raw_body, signature)
    duplicate = _post_webhook(api, raw_body, signature)

    assert first.status_code == duplicate.status_code == 200
    assert json_object(first).get("status") == "processed"
    assert json_object(duplicate) == {"status": "duplicate", "eventId": event["id"]}
    events = webhook_events_from_state(api.state())
    assert len(events) == 1
    assert events[0].get("id") == event["id"]


def test_old_replayed_event_is_rejected_by_timestamp_tolerance(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    old_timestamp = int(time.time()) - 600
    raw_body = _raw_json(
        _invoice_paid_event(api, resources, timestamp=old_timestamp)
    )

    response = _post_webhook(
        api,
        raw_body,
        _signature(settings.webhook_secret, old_timestamp, raw_body),
    )

    assert response.status_code == 401
    _assert_open_invoice_and_no_claimed_event(api, resources)


def test_unknown_signed_event_is_recorded_as_ignored(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    now = int(time.time())
    invoice_id = resources.user_a.invoice_id
    assert invoice_id is not None
    before = invoice_from_state(api.state(), invoice_id)
    assert before is not None
    event = {
        "id": f"evt_{uuid4().hex}",
        "type": "synthetic.unknown",
        "created": now,
    }
    raw_body = _raw_json(event)

    response = _post_webhook(
        api,
        raw_body,
        _signature(settings.webhook_secret, now, raw_body),
    )

    assert response.status_code == 200
    assert json_object(response) == {"status": "ignored", "eventId": event["id"]}
    state = api.state()
    assert invoice_from_state(state, invoice_id) == before
    events = webhook_events_from_state(state)
    assert len(events) == 1
    assert events[0].get("status") == "ignored"


def test_body_modified_after_signing_is_rejected(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    now = int(time.time())
    original = _raw_json(_invoice_paid_event(api, resources, timestamp=now))
    modified = original + b" "

    response = _post_webhook(
        api,
        modified,
        _signature(settings.webhook_secret, now, original),
    )

    assert response.status_code == 401
    _assert_open_invoice_and_no_claimed_event(api, resources)


def test_valid_signature_cannot_override_server_side_amount_binding(
    api: LabApiClient,
    resources: SeedResources,
    settings: SecurityTestSettings,
) -> None:
    now = int(time.time())
    event = _invoice_paid_event(api, resources, timestamp=now)
    data = event["data"]
    assert isinstance(data, dict)
    invoice_object = data["object"]
    assert isinstance(invoice_object, dict)
    amount = invoice_object["amountCents"]
    assert isinstance(amount, int)
    invoice_object["amountCents"] = amount + 1
    raw_body = _raw_json(event)

    response = _post_webhook(
        api,
        raw_body,
        _signature(settings.webhook_secret, now, raw_body),
    )

    assert response.status_code == 400
    invoice_id = resources.user_a.invoice_id
    assert invoice_id is not None
    unchanged_invoice = invoice_from_state(api.state(), invoice_id)
    assert unchanged_invoice is not None
    assert unchanged_invoice.get("state") == "open"
    assert webhook_events_from_state(api.state()) == []
