from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from .clients.lab_api import LabApiClient
from .fixtures.identities import IdentityCatalog

pytestmark = pytest.mark.security_integration


@dataclass(frozen=True, slots=True)
class RateLimitCase:
    case_id: str
    path: str
    payload: dict[str, Any]
    limit: int
    accepted_status: int


def _cases(identities: IdentityCatalog) -> tuple[RateLimitCase, ...]:
    return (
        RateLimitCase(
            "login",
            "/auth/login",
            {
                "email": identities.unknown.email,
                "password": identities.unknown.password,
            },
            5,
            401,
        ),
        RateLimitCase(
            "reset-password",
            "/auth/reset-password",
            {"email": identities.unknown.email},
            3,
            202,
        ),
        RateLimitCase(
            "public-contact",
            "/public/contact",
            {
                "email": identities.unknown.email,
                "subject": "Synthetic local request",
                "message": "A deterministic message used to test a bounded public form.",
                "context": {"sourceUrl": "https://example.test/form", "urgency": 1},
            },
            4,
            202,
        ),
    )


@pytest.mark.parametrize("case_index", [0, 1, 2], ids=["login", "reset", "public-form"])
def test_rate_limit_is_deterministic_and_returns_retry_contract(
    case_index: int,
    api: LabApiClient,
    identities: IdentityCatalog,
) -> None:
    case = _cases(identities)[case_index]

    accepted = [api.request("POST", case.path, json=case.payload) for _ in range(case.limit)]
    blocked = api.request("POST", case.path, json=case.payload)

    assert all(response.status_code == case.accepted_status for response in accepted)
    assert blocked.status_code == 429
    assert blocked.headers.get("x-ratelimit-limit") == str(case.limit)
    assert blocked.headers.get("x-ratelimit-remaining") == "0"
    retry_after = blocked.headers.get("retry-after")
    assert retry_after is not None and retry_after.isdigit()
    assert 1 <= int(retry_after) <= 60


def test_expensive_ai_boundary_has_a_small_deterministic_quota(
    api: LabApiClient,
    identities: IdentityCatalog,
) -> None:
    token = api.login(identities.user_a)
    payload = {
        "text": "A bounded synthetic document for deterministic quota verification.",
        "source": {"kind": "inline"},
    }

    accepted = [
        api.request("POST", "/ai/parse", token=token, json=payload)
        for _ in range(2)
    ]
    blocked = api.request("POST", "/ai/parse", token=token, json=payload)

    assert all(response.status_code == 201 for response in accepted)
    assert blocked.status_code == 429
    assert blocked.headers.get("x-ratelimit-limit") == "2"
    assert blocked.headers.get("x-ratelimit-remaining") == "0"
    assert blocked.headers.get("retry-after", "").isdigit()
