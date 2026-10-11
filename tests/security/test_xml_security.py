from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from .clients.lab_api import LabApiClient, json_object
from .fixtures.identities import Actor

pytestmark = pytest.mark.security_integration

_FIXTURES = Path(__file__).parent / "fixtures" / "xml"


def _post_xml(
    api: LabApiClient,
    token: str,
    body: bytes,
    content_type: str = "application/xml",
) -> httpx.Response:
    return api.request(
        "POST",
        "/imports/xml",
        token=token,
        content=body,
        headers={"Content-Type": content_type},
    )


def test_valid_bounded_xml_is_accepted_without_echoing_content(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    body = (_FIXTURES / "valid-properties.xml").read_bytes()

    response = _post_xml(api, tokens[Actor.USER_A], body)

    assert response.status_code == 201
    payload = json_object(response)
    assert payload.get("accepted") is True
    assert payload.get("rootElement") == "properties"
    assert "Synthetic regression property" not in response.text


@pytest.mark.parametrize(
    "fixture_name",
    ["forbidden-dtd.xml", "forbidden-external-entity.xml"],
    ids=["dtd", "external-entity"],
)
def test_dtd_and_external_entities_are_rejected(
    fixture_name: str,
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _post_xml(
        api,
        tokens[Actor.USER_A],
        (_FIXTURES / fixture_name).read_bytes(),
    )

    assert response.status_code == 400


def test_oversized_xml_is_rejected_before_parsing(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    body = f"<properties>{'x' * 32_768}</properties>".encode()

    response = _post_xml(api, tokens[Actor.USER_A], body)

    assert response.status_code == 413


def test_excessive_xml_nesting_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    body = ("<n>" * 9 + "</n>" * 9).encode()

    response = _post_xml(api, tokens[Actor.USER_A], body, "text/xml")

    assert response.status_code == 400


def test_excessive_xml_node_count_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    body = f"<properties>{'<property />' * 128}</properties>".encode()

    response = _post_xml(api, tokens[Actor.USER_A], body)

    assert response.status_code == 400


def test_xml_endpoint_rejects_wrong_content_type(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _post_xml(
        api,
        tokens[Actor.USER_A],
        b"<properties />",
        "text/plain",
    )

    assert response.status_code == 415
