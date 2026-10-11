from __future__ import annotations

from collections.abc import Iterator

import pytest

from .clients.lab_api import LabApiClient
from .config import SecurityTestSettings
from .fixtures.identities import Actor, IdentityCatalog
from .fixtures.state import SeedResources


@pytest.fixture(scope="session")
def settings() -> SecurityTestSettings:
    # BaseSettings resolves required values from the environment at runtime;
    # the generated Pydantic constructor signature is intentionally stricter.
    return SecurityTestSettings()  # type: ignore[call-arg]


@pytest.fixture(scope="session")
def api(settings: SecurityTestSettings) -> Iterator[LabApiClient]:
    with LabApiClient(settings) as client:
        yield client


@pytest.fixture(scope="session")
def identities(settings: SecurityTestSettings) -> IdentityCatalog:
    return IdentityCatalog.from_settings(settings)


@pytest.fixture(autouse=True)
def isolated_lab(api: LabApiClient) -> Iterator[None]:
    """Every test starts from known users, resources, mailbox, logs, and rate buckets."""

    api.reset()
    yield


@pytest.fixture()
def resources(api: LabApiClient) -> SeedResources:
    return SeedResources.from_state(api.state())


@pytest.fixture()
def tokens(api: LabApiClient, identities: IdentityCatalog) -> dict[Actor, str]:
    return {
        Actor.USER_A: api.login(identities.user_a),
        Actor.USER_B: api.login(identities.user_b),
        Actor.ADMIN: api.login(identities.admin),
    }
