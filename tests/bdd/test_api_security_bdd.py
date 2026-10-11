from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.security.clients.lab_api import LabApiClient, json_object
from tests.security.config import SecurityTestSettings
from tests.security.fixtures.identities import IdentityCatalog
from tests.security.fixtures.state import (
    SeedResources,
    invoice_from_state,
    property_from_state,
    webhook_events_from_state,
)

pytestmark = pytest.mark.security_integration
scenarios(
    "features/ownership.feature",
    "features/mass_assignment.feature",
    "features/webhook_integrity.feature",
)


@dataclass(frozen=True)
class PropertyCase:
    property_id: str
    other_owner_id: str
    tokens: dict[str, str]
    before: dict[str, Any]


@dataclass(frozen=True)
class PaymentCase:
    invoice_id: str
    raw: bytes
    signature: str | None


@given("the synthetic lab starts from a clean state")
def fresh_lab(api: LabApiClient) -> None:
    api.reset()


@given("two customers and a property owned by the first customer", target_fixture="property_case")
def owned_property(api: LabApiClient, identities: IdentityCatalog) -> PropertyCase:
    resources = SeedResources.from_state(api.state())
    property_id = resources.user_a.property_id
    assert property_id is not None
    before = property_from_state(api.state(), property_id)
    assert before is not None
    return PropertyCase(
        property_id,
        resources.user_b.user_id,
        {"owner": api.login(identities.user_a), "other": api.login(identities.user_b)},
        before,
    )


@when(
    parsers.parse('the "{actor}" customer sends "{method}" for that property'),
    target_fixture="response",
)
def access_property(
    api: LabApiClient, property_case: PropertyCase, actor: str, method: str
) -> httpx.Response:
    assert actor in {"owner", "other"} and method in {"GET", "PATCH"}
    body = {"title": "Unauthorized BDD change"} if method == "PATCH" else None
    return api.request(
        method,
        f"/properties/{property_case.property_id}",
        token=property_case.tokens[actor],
        json=body,
    )


@when(
    parsers.parse('the owner includes the protected field "{field}" in an otherwise valid update'),
    target_fixture="response",
)
def protected_update(api: LabApiClient, property_case: PropertyCase, field: str) -> httpx.Response:
    values: dict[str, object] = {
        "ownerId": property_case.other_owner_id,
        "role": "admin",
        "isVerified": True,
    }
    assert field in values
    return api.request(
        "PATCH",
        f"/properties/{property_case.property_id}",
        token=property_case.tokens["owner"],
        json={"title": "Valid field must not partially apply", field: values[field]},
    )


@then(parsers.parse("the API returns HTTP {status:d}"))
def response_status(response: httpx.Response, status: int) -> None:
    assert response.status_code == status


@then("the original property remains unchanged")
def unchanged_property(api: LabApiClient, property_case: PropertyCase) -> None:
    assert property_from_state(api.state(), property_case.property_id) == property_case.before


@given(
    parsers.parse('a "{kind}" payment notification for an open synthetic invoice'),
    target_fixture="payment_case",
)
def payment_event(api: LabApiClient, settings: SecurityTestSettings, kind: str) -> PaymentCase:
    assert kind in {"valid", "missing", "forged", "stale"}
    invoice_id = SeedResources.from_state(api.state()).user_a.invoice_id
    assert invoice_id is not None
    invoice = invoice_from_state(api.state(), invoice_id)
    assert invoice is not None and invoice["state"] == "open"
    timestamp = int(time.time()) - (1000 if kind == "stale" else 0)
    payload = {
        "id": f"evt_{uuid4().hex}",
        "type": "invoice.paid",
        "created": timestamp,
        "data": {
            "object": {
                "invoiceId": invoice_id,
                "orderId": invoice["orderId"],
                "amountCents": invoice["amountCents"],
                "currency": invoice["currency"],
            }
        },
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hmac.new(
        settings.webhook_secret.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256
    ).hexdigest()
    if kind == "forged":
        digest = "0" * 64
    signature = None if kind == "missing" else f"t={timestamp},v1={digest}"
    return PaymentCase(invoice_id, raw, signature)


@when("the payment notification is received", target_fixture="response")
@when("the same payment notification is received again", target_fixture="response")
def receive_payment(api: LabApiClient, payment_case: PaymentCase) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if payment_case.signature is not None:
        headers["stripe-signature"] = payment_case.signature
    return api.request("POST", "/webhooks/stripe", content=payment_case.raw, headers=headers)


@then("the invoice remains open with no claimed events")
def invoice_unchanged(api: LabApiClient, payment_case: PaymentCase) -> None:
    invoice = invoice_from_state(api.state(), payment_case.invoice_id)
    assert invoice is not None and invoice["state"] == "open"
    assert webhook_events_from_state(api.state()) == []


@then("the invoice is paid with exactly one claimed event")
def invoice_paid_once(api: LabApiClient, payment_case: PaymentCase) -> None:
    invoice = invoice_from_state(api.state(), payment_case.invoice_id)
    assert invoice is not None and invoice["state"] == "paid"
    assert len(webhook_events_from_state(api.state())) == 1


@then("the response identifies a duplicate")
def duplicate_event(response: httpx.Response) -> None:
    assert json_object(response)["status"] == "duplicate"
