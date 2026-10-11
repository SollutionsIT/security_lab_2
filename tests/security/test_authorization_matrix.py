from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import pytest

from .clients.lab_api import LabApiClient
from .data.authorization_matrix import (
    AUTHORIZATION_CASES,
    Action,
    AuthorizationCase,
    ResourceKind,
)
from .fixtures.identities import Actor
from .fixtures.state import (
    SeedResources,
    event_list,
    invoice_from_state,
    property_from_state,
)

pytestmark = pytest.mark.security_integration


def _resource_id(case: AuthorizationCase, resources: SeedResources) -> str | None:
    if case.resource_owner is None:
        return None
    alias = resources.for_actor(case.resource_owner)
    if case.resource is ResourceKind.PROPERTY:
        return alias.property_id
    if case.resource is ResourceKind.INVOICE:
        return alias.invoice_id
    return None


def _perform(
    case: AuthorizationCase,
    api: LabApiClient,
    tokens: dict[Actor, str],
    resource_id: str | None,
    correlation_id: str,
) -> httpx.Response:
    token = tokens.get(case.actor)
    headers = {"X-Correlation-ID": correlation_id}
    if case.resource is ResourceKind.ADMIN_AUDIT:
        return api.request(
            "GET",
            "/admin/audit-events",
            token=token,
            headers=headers,
        )
    if resource_id is None:
        raise AssertionError(f"Case {case.case_id} has no resource id")
    if case.resource is ResourceKind.INVOICE:
        return api.request(
            "GET",
            f"/invoices/{resource_id}",
            token=token,
            headers=headers,
        )
    if case.action is Action.READ:
        return api.request(
            "GET",
            f"/properties/{resource_id}",
            token=token,
            headers=headers,
        )
    if case.action is Action.UPDATE:
        return api.request(
            "PATCH",
            f"/properties/{resource_id}",
            token=token,
            headers=headers,
            json={"title": f"Matrix update {case.case_id}"},
        )
    if case.action is Action.DELETE:
        return api.request(
            "DELETE",
            f"/properties/{resource_id}",
            token=token,
            headers=headers,
        )
    raise AssertionError(f"Unsupported authorization action {case.action.value}")


@pytest.mark.parametrize(
    "case",
    AUTHORIZATION_CASES,
    ids=[case.case_id for case in AUTHORIZATION_CASES],
)
def test_authorization_matrix_enforces_decision_side_effects_and_audit(
    case: AuthorizationCase,
    api: LabApiClient,
    resources: SeedResources,
    tokens: dict[Actor, str],
) -> None:
    resource_id = _resource_id(case, resources)
    if (
        case.resource is ResourceKind.PROPERTY
        and case.resource_state == "archived"
        and case.resource_owner is not None
        and resource_id is not None
    ):
        archived = api.request(
            "PATCH",
            f"/properties/{resource_id}",
            token=tokens[case.resource_owner],
            json={"state": "archived"},
        )
        assert archived.status_code == 200
    before_state = api.state()
    before_property = (
        property_from_state(before_state, resource_id)
        if case.resource is ResourceKind.PROPERTY and resource_id is not None
        else None
    )
    before_invoice = (
        invoice_from_state(before_state, resource_id)
        if case.resource is ResourceKind.INVOICE and resource_id is not None
        else None
    )

    correlation_id = f"matrix-{case.case_id}"
    response = _perform(case, api, tokens, resource_id, correlation_id)
    assert response.headers.get("x-correlation-id") == correlation_id
    if response.status_code == 404:
        protected_values: list[object] = []
        if before_property is not None:
            protected_values.extend(
                before_property.get(field)
                for field in ("ownerId", "title", "description", "listingUrl")
            )
        if before_invoice is not None:
            protected_values.extend(
                before_invoice.get(field)
                for field in ("ownerId", "orderId", "amountCents")
            )
        assert all(
            str(value) not in response.text
            for value in protected_values
            if value is not None
        )
        nonexistent = _perform(
            case,
            api,
            tokens,
            f"missing-{uuid4().hex}",
            f"hidden-{uuid4().hex}",
        )
        assert nonexistent.status_code == 404
        assert nonexistent.json() == response.json()
    after_state = api.state()

    assert response.status_code == case.expected_status
    if response.status_code == 204:
        assert response.content == b""

    if case.resource is ResourceKind.PROPERTY and resource_id is not None:
        after_property = property_from_state(after_state, resource_id)
        assert before_property is not None
        assert before_property.get("state") == case.resource_state
        if not case.allowed:
            assert after_property == before_property
        elif case.action is Action.UPDATE:
            assert after_property is not None
            assert after_property.get("title") == f"Matrix update {case.case_id}"
            assert after_property.get("ownerId") == before_property.get("ownerId")
        elif case.action is Action.DELETE:
            assert after_property is None
        else:
            assert after_property == before_property

    if case.resource is ResourceKind.INVOICE and resource_id is not None:
        after_invoice = invoice_from_state(after_state, resource_id)
        assert before_invoice is not None
        assert before_invoice.get("state") == case.resource_state
        assert after_invoice == before_invoice

    if case.resource is ResourceKind.ADMIN_AUDIT:
        assert after_state == before_state

    events = event_list(api.logs())
    audit_events: list[dict[str, Any]] = [
        event for event in events if event.get("event") == "authorization_denied"
    ]
    if case.expected_audit_action is None:
        assert not audit_events
        return

    actor_id = resources.for_actor(case.actor).user_id
    expected_resource_type = (
        "admin_function" if case.resource is ResourceKind.ADMIN_AUDIT else case.resource.value
    )
    expected_resource_id = (
        "audit-events" if case.resource is ResourceKind.ADMIN_AUDIT else resource_id
    )
    expected_reason = {
        ResourceKind.PROPERTY: "owner_role_or_state_policy",
        ResourceKind.INVOICE: "not_owner_or_admin",
        ResourceKind.ADMIN_AUDIT: "insufficient_role",
    }[case.resource]
    matching_events = [
        event
        for event in audit_events
        if (
            event.get("actor_id") == actor_id
            and event.get("resource_type") == expected_resource_type
            and event.get("resource_id") == expected_resource_id
            and event.get("action") == case.expected_audit_action
            and event.get("result") == "denied"
            and event.get("correlation_id") == correlation_id
            and event.get("reason") == expected_reason
        )
    ]
    assert len(audit_events) == 1
    assert len(matching_events) == 1
