from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest

from .clients.lab_api import LabApiClient, json_object
from .fixtures.identities import Actor
from .fixtures.state import event_list

pytestmark = pytest.mark.security_integration

_SAFE_PDF_PATH = Path(__file__).parent / "fixtures" / "files" / "safe-document.pdf"
_MAX_UPLOAD_BYTES = 1_048_576
_SERVER_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.pdf$"
)


def _upload(
    api: LabApiClient,
    token: str,
    *,
    filename: str,
    content: bytes,
    media_type: str,
) -> httpx.Response:
    return api.request(
        "POST",
        "/uploads",
        token=token,
        files={"file": (filename, content, media_type)},
    )


def _assert_no_accepted_upload_event(api: LabApiClient) -> None:
    assert not any(
        event.get("event") == "file_upload_accepted"
        for event in event_list(api.logs())
    )


def test_valid_file_uses_server_name_and_safe_download_headers(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    content = _SAFE_PDF_PATH.read_bytes()

    uploaded = _upload(
        api,
        tokens[Actor.USER_A],
        filename="safe-document.pdf",
        content=content,
        media_type="application/pdf",
    )

    assert uploaded.status_code == 201
    receipt = json_object(uploaded)
    attachment_id = receipt.get("attachmentId")
    stored_name = receipt.get("storedName")
    assert isinstance(attachment_id, str)
    assert isinstance(stored_name, str)
    assert _SERVER_NAME.fullmatch(stored_name)
    assert stored_name.startswith(attachment_id)
    assert "safe-document" not in stored_name
    assert receipt.get("mediaType") == "application/pdf"
    assert receipt.get("sizeBytes") == len(content)
    assert any(
        event.get("event") == "file_upload_accepted"
        and event.get("resource_id") == attachment_id
        for event in event_list(api.logs())
    )

    downloaded = api.request(
        "GET",
        f"/uploads/{stored_name}",
        token=tokens[Actor.USER_A],
    )
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert downloaded.headers.get("content-type") == "application/pdf"
    assert downloaded.headers.get("content-disposition") == 'attachment; filename="download.pdf"'
    assert downloaded.headers.get("x-content-type-options") == "nosniff"
    assert downloaded.headers.get("content-security-policy") == "default-src 'none'; sandbox"
    assert downloaded.headers.get("cache-control") == "private, no-store"
    assert downloaded.headers.get("content-length") == str(len(content))

    cross_owner = api.request(
        "GET",
        f"/uploads/{stored_name}",
        token=tokens[Actor.USER_B],
    )
    anonymous = api.request("GET", f"/uploads/{stored_name}")
    administrator = api.request(
        "GET",
        f"/uploads/{stored_name}",
        token=tokens[Actor.ADMIN],
    )
    assert cross_owner.status_code == 404
    assert anonymous.status_code == 401
    assert administrator.status_code == 200
    assert administrator.content == content
    assert any(
        event.get("event") == "authorization_denied"
        and event.get("resource_type") == "attachment"
        and event.get("action") == "read"
        for event in event_list(api.logs())
    )


def test_oversized_file_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    content = b"%PDF-" + b"A" * _MAX_UPLOAD_BYTES

    response = _upload(
        api,
        tokens[Actor.USER_A],
        filename="oversized.pdf",
        content=content,
        media_type="application/pdf",
    )

    assert response.status_code == 413
    _assert_no_accepted_upload_event(api)


def test_wrong_client_mime_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _upload(
        api,
        tokens[Actor.USER_A],
        filename="safe-document.pdf",
        content=_SAFE_PDF_PATH.read_bytes(),
        media_type="image/png",
    )

    assert response.status_code == 400
    _assert_no_accepted_upload_event(api)


def test_extension_and_magic_bytes_mismatch_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _upload(
        api,
        tokens[Actor.USER_A],
        filename="mismatch.png",
        content=_SAFE_PDF_PATH.read_bytes(),
        media_type="image/png",
    )

    assert response.status_code == 400
    _assert_no_accepted_upload_event(api)


def test_path_traversal_filename_is_rejected_before_storage(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _upload(
        api,
        tokens[Actor.USER_A],
        filename="../escape.pdf",
        content=_SAFE_PDF_PATH.read_bytes(),
        media_type="application/pdf",
    )

    assert response.status_code == 400
    _assert_no_accepted_upload_event(api)


def test_empty_file_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _upload(
        api,
        tokens[Actor.USER_A],
        filename="empty.pdf",
        content=b"",
        media_type="application/pdf",
    )

    assert response.status_code == 400
    _assert_no_accepted_upload_event(api)


def test_unsupported_file_type_is_rejected(
    api: LabApiClient,
    tokens: dict[Actor, str],
) -> None:
    response = _upload(
        api,
        tokens[Actor.USER_A],
        filename="unsupported.txt",
        content=b"Synthetic inert plain text.",
        media_type="text/plain",
    )

    assert response.status_code == 400
    _assert_no_accepted_upload_event(api)
