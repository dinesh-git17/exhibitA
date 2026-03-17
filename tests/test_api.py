"""Smoke tests for app-facing API endpoints per Design Doc 7.3."""

# pylint: disable=redefined-outer-name,missing-class-docstring,missing-function-docstring,import-outside-toplevel

import os
import sqlite3
import uuid
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

_TEST_KEY_DINESH = "test-key-dinesh-0123456789abcdef"  # gitleaks:allow
_TEST_KEY_CAROLINA = "test-key-carolina-0123456789abcdef"  # gitleaks:allow


def _auth_headers(signer: str = "dinesh") -> dict[str, str]:
    key = _TEST_KEY_DINESH if signer == "dinesh" else _TEST_KEY_CAROLINA
    return {"Authorization": f"Bearer {key}"}


def _seed_api_keys(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    for signer, raw_key in [
        ("dinesh", _TEST_KEY_DINESH),
        ("carolina", _TEST_KEY_CAROLINA),
    ]:
        key_hash = bcrypt.hashpw(
            raw_key.encode("utf-8"), bcrypt.gensalt(rounds=4)
        ).decode("utf-8")
        conn.execute(
            "INSERT INTO api_keys (id, signer, key_hash) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), signer, key_hash),
        )
    conn.commit()
    conn.close()


@pytest.fixture()
def app_client(tmp_path: Path) -> Iterator[tuple[TestClient, Path]]:
    """Create a fresh app with an isolated test database and seeded API keys."""
    db_path = tmp_path / "test.db"
    with patch.dict(os.environ, {"DATABASE_PATH": str(db_path)}):
        from app import create_app

        app = create_app()
        with TestClient(app) as client:
            _seed_api_keys(db_path)
            yield client, db_path


def _seed_content(
    db_path: Path,
    content_id: str,
    content_type: str = "contract",
    section_order: int = 1,
    title: str = "Test",
    body: str = "Test body",
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO content (id, type, title, body, section_order) "
        "VALUES (?, ?, ?, ?, ?)",
        (content_id, content_type, title, body, section_order),
    )
    conn.commit()
    conn.close()


def _seed_signature(
    db_path: Path,
    signature_id: str,
    content_id: str,
    signer: str = "dinesh",
    image: bytes = b"\x89PNG\r\n",
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO signatures (id, content_id, signer, image) VALUES (?, ?, ?, ?)",
        (signature_id, content_id, signer, image),
    )
    conn.commit()
    conn.close()


# --- Auth tests ---


class TestAuth:
    def test_missing_auth_returns_401(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/content")
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "UNAUTHORIZED"
        assert "message" in body["error"]

    def test_invalid_key_returns_401(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get(
            "/content", headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"

    def test_valid_key_grants_access(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/content", headers=_auth_headers())
        assert response.status_code == 200

    def test_health_remains_unauthenticated(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/health")
        assert response.status_code == 200

    def test_signer_mismatch_returns_400(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        png = BytesIO(b"\x89PNG\r\ntest")
        response = client.post(
            "/signatures",
            data={"content_id": "c1", "signer": "dinesh"},
            files={"image": ("sig.png", png, "image/png")},
            headers=_auth_headers("carolina"),
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_SIGNER"

    def test_get_endpoints_protected(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        for path in [
            "/content",
            "/content/x",
            "/content/x/signatures",
            "/signatures/x/image",
            "/sync",
        ]:
            response = client.get(path)
            assert response.status_code == 401, f"GET {path} not protected"

    def test_post_endpoints_protected(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        sig_response = client.post(
            "/signatures",
            data={"content_id": "x", "signer": "dinesh"},
            files={"image": ("sig.png", BytesIO(b"\x89PNG"), "image/png")},
        )
        assert sig_response.status_code == 401
        token_response = client.post(
            "/device-tokens",
            json={"signer": "dinesh", "token": "test"},
        )
        assert token_response.status_code == 401


# --- Existing endpoint tests (with auth) ---


class TestHealth:
    def test_health_returns_ok(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestContentList:
    def test_empty_content(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/content", headers=_auth_headers())
        assert response.status_code == 200
        assert response.json() == {"items": []}

    def test_content_ordered_by_type_and_section(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        _seed_content(db_path, "t1", "thought", 1)
        _seed_content(db_path, "c1", "contract", 1)
        _seed_content(db_path, "l1", "letter", 1)
        response = client.get("/content", headers=_auth_headers())
        items = response.json()["items"]
        assert [i["type"] for i in items] == ["contract", "letter", "thought"]

    def test_filter_by_type(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        _seed_content(db_path, "l1", "letter", 1)
        response = client.get("/content?type=contract", headers=_auth_headers())
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "contract"

    def test_filter_by_since(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        response = client.get(
            "/content?since=2099-01-01T00:00:00Z", headers=_auth_headers()
        )
        assert response.json() == {"items": []}


class TestContentDetail:
    def test_existing_content(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        response = client.get("/content/c1", headers=_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "c1"
        assert data["type"] == "contract"

    def test_missing_content_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/content/nonexistent", headers=_auth_headers())
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"


class TestContentSignatures:
    def test_signatures_for_content(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        _seed_signature(db_path, "s1", "c1", "dinesh")
        response = client.get("/content/c1/signatures", headers=_auth_headers())
        assert response.status_code == 200
        sigs = response.json()
        assert len(sigs) == 1
        assert sigs[0]["signer"] == "dinesh"
        assert "image" not in sigs[0]

    def test_missing_content_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get(
            "/content/nonexistent/signatures", headers=_auth_headers()
        )
        assert response.status_code == 404


class TestSignatureImage:
    def test_returns_png(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        png_data = b"\x89PNG\r\ntest"
        _seed_signature(db_path, "s1", "c1", "dinesh", png_data)
        response = client.get("/signatures/s1/image", headers=_auth_headers())
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == png_data

    def test_missing_signature_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/signatures/nonexistent/image", headers=_auth_headers())
        assert response.status_code == 404


class TestCreateSignature:
    def test_successful_upload(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        png = BytesIO(b"\x89PNG\r\ntest")
        response = client.post(
            "/signatures",
            data={"content_id": "c1", "signer": "dinesh"},
            files={"image": ("sig.png", png, "image/png")},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["content_id"] == "c1"
        assert body["signer"] == "dinesh"
        assert "id" in body
        assert "signed_at" in body

    def test_duplicate_returns_409(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        _seed_signature(db_path, "s1", "c1", "dinesh")
        png = BytesIO(b"\x89PNG\r\ntest")
        response = client.post(
            "/signatures",
            data={"content_id": "c1", "signer": "dinesh"},
            files={"image": ("sig.png", png, "image/png")},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "ALREADY_SIGNED"

    def test_oversized_payload_returns_413(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        oversized = BytesIO(b"\x00" * (1_048_576 + 1))
        response = client.post(
            "/signatures",
            data={"content_id": "c1", "signer": "dinesh"},
            files={"image": ("sig.png", oversized, "image/png")},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_sync_log_created_on_signature(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        png = BytesIO(b"\x89PNG\r\ntest")
        sig_response = client.post(
            "/signatures",
            data={"content_id": "c1", "signer": "carolina"},
            files={"image": ("sig.png", png, "image/png")},
            headers=_auth_headers("carolina"),
        )
        sig_id = sig_response.json()["id"]
        sync_response = client.get("/sync", headers=_auth_headers())
        changes = sync_response.json()["changes"]
        assert len(changes) == 1
        assert changes[0]["entity_type"] == "signature"
        assert changes[0]["entity_id"] == sig_id
        assert changes[0]["action"] == "create"


class TestSync:
    def test_empty_sync(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/sync", headers=_auth_headers())
        assert response.status_code == 200
        assert response.json() == {"changes": []}

    def test_sync_with_since_filter(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get(
            "/sync?since=2099-01-01T00:00:00Z", headers=_auth_headers()
        )
        assert response.status_code == 200
        assert response.json() == {"changes": []}


class TestDeviceTokens:
    def test_register_token(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.post(
            "/device-tokens",
            json={"signer": "dinesh", "token": "abc123"},
            headers=_auth_headers(),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["signer"] == "dinesh"
        assert body["token"] == "abc123"
        assert "id" in body
        assert "registered_at" in body

    def test_duplicate_token_updates(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        client.post(
            "/device-tokens",
            json={"signer": "dinesh", "token": "abc123"},
            headers=_auth_headers(),
        )
        response = client.post(
            "/device-tokens",
            json={"signer": "carolina", "token": "abc123"},
            headers=_auth_headers("carolina"),
        )
        assert response.status_code == 201
        assert response.json()["signer"] == "carolina"


class TestComments:
    def test_create_comment_success(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "Beautiful."},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == cid
        assert data["signer"] == "dinesh"
        assert data["body"] == "Beautiful."
        assert "created_at" in data

    def test_create_comment_duplicate_returns_409(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "First."},
            headers=_auth_headers("dinesh"),
        )
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "Second."},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "ALREADY_COMMENTED"

    def test_create_comment_wrong_signer_returns_400(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "carolina", "body": "Nope."},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_SIGNER"

    def test_create_comment_on_contract_returns_422(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="contract")
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "No."},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_CONTENT_TYPE"

    def test_create_comment_nonexistent_content_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.post(
            "/comments",
            json={"content_id": "missing", "signer": "dinesh", "body": "X"},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 404

    def test_create_comment_empty_body_returns_422(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="thought")
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": ""},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 422

    def test_create_comment_exceeds_max_length_returns_422(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "x" * 2001},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 422

    def test_get_content_comments_empty(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        response = client.get(f"/content/{cid}/comments", headers=_auth_headers())
        assert response.status_code == 200
        assert response.json() == []

    def test_get_content_comments_returns_filed(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="thought")
        client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "Noted."},
            headers=_auth_headers("dinesh"),
        )
        response = client.get(f"/content/{cid}/comments", headers=_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["body"] == "Noted."

    def test_create_comment_writes_sync_log(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        response = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "Logged."},
            headers=_auth_headers("dinesh"),
        )
        assert response.status_code == 201
        comment_id = response.json()["id"]
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT entity_type, entity_id, action FROM sync_log WHERE entity_id = ?",
            (comment_id,),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "comment"
        assert row[2] == "create"

    def test_both_signers_can_comment_on_same_content(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        cid = str(uuid.uuid4())
        _seed_content(db_path, cid, content_type="letter")
        r1 = client.post(
            "/comments",
            json={"content_id": cid, "signer": "dinesh", "body": "Mine."},
            headers=_auth_headers("dinesh"),
        )
        r2 = client.post(
            "/comments",
            json={"content_id": cid, "signer": "carolina", "body": "Yours."},
            headers=_auth_headers("carolina"),
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        response = client.get(f"/content/{cid}/comments", headers=_auth_headers())
        assert len(response.json()) == 2


class TestErrorEnvelope:
    def test_404_uses_standard_envelope(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/content/missing", headers=_auth_headers())
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
