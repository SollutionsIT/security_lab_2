from __future__ import annotations

import pytest

from .clients.lab_api import LabApiClient
from .fixtures.identities import Actor
from .fixtures.state import SeedResources, property_from_state

pytestmark = pytest.mark.security_integration


@pytest.mark.parametrize(
    "forbidden_field_names",
    [
        ("role",),
        ("ownerId",),
        ("isVerified",),
        ("role", "ownerId", "isVerified"),
    ],
    ids=["role", "owner-id", "verification", "combined"],
)
def test_property_update_rejects_mass_assignment_without_side_effects(
    forbidden_field_names: tuple[str, ...],
    api: LabApiClient,
    resources: SeedResources,
    tokens: dict[Actor, str],
) -> None:
    property_id = resources.user_a.property_id
    assert property_id is not None
    before = property_from_state(api.state(), property_id)
    forbidden_values: dict[str, object] = {
        "role": "admin",
        "ownerId": resources.user_b.user_id,
        "isVerified": True,
    }
    forbidden_fields = {
        name: forbidden_values[name] for name in forbidden_field_names
    }

    response = api.request(
        "PATCH",
        f"/properties/{property_id}",
        token=tokens[Actor.USER_A],
        json={"title": "Allowed title must not partially apply", **forbidden_fields},
    )

    assert response.status_code == 400
    assert property_from_state(api.state(), property_id) == before


def test_nested_mass_assignment_is_rejected_without_partial_update(
    api: LabApiClient,
    resources: SeedResources,
    tokens: dict[Actor, str],
) -> None:
    property_id = resources.user_a.property_id
    assert property_id is not None
    before = property_from_state(api.state(), property_id)

    response = api.request(
        "PATCH",
        f"/properties/{property_id}",
        token=tokens[Actor.USER_A],
        json={
            "address": {
                "city": "Synthetic City",
                "countryCode": "AT",
                "ownerId": resources.user_b.user_id,
            }
        },
    )

    assert response.status_code == 400
    assert property_from_state(api.state(), property_id) == before
