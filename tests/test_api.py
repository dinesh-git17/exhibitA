"""Smoke tests for app-facing API endpoints per Design Doc 7.3."""

import os
import sqlite3
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_client(tmp_path: Path) -> Iterator[tuple[TestClient, Path]]:
    """Create a fresh app with an isolated test database."""
    db_path = tmp_path / "test.db"
    with patch.dict(os.environ, {"DATABASE_PATH": str(db_path)}):
        from app import create_app

        app = create_app()
        with TestClient(app) as client:
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


class TestHealth:
    def test_health_returns_ok(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestContentList:
    def test_empty_content(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/content")
        assert response.status_code == 200
        assert response.json() == {"items": []}

    def test_content_ordered_by_type_and_section(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = app_client
        _seed_content(db_path, "t1", "thought", 1)
        _seed_content(db_path, "c1", "contract", 1)
        _seed_content(db_path, "l1", "letter", 1)
        response = client.get("/content")
        items = response.json()["items"]
        assert [i["type"] for i in items] == ["contract", "letter", "thought"]

    def test_filter_by_type(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        _seed_content(db_path, "l1", "letter", 1)
        response = client.get("/content?type=contract")
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "contract"

    def test_filter_by_since(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        response = client.get("/content?since=2099-01-01T00:00:00Z")
        assert response.json() == {"items": []}


class TestContentDetail:
    def test_existing_content(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        response = client.get("/content/c1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "c1"
        assert data["type"] == "contract"

    def test_missing_content_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/content/nonexistent")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"


class TestContentSignatures:
    def test_signatures_for_content(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        _seed_signature(db_path, "s1", "c1", "dinesh")
        response = client.get("/content/c1/signatures")
        assert response.status_code == 200
        sigs = response.json()
        assert len(sigs) == 1
        assert sigs[0]["signer"] == "dinesh"
        assert "image" not in sigs[0]

    def test_missing_content_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/content/nonexistent/signatures")
        assert response.status_code == 404


class TestSignatureImage:
    def test_returns_png(self, app_client: tuple[TestClient, Path]) -> None:
        client, db_path = app_client
        _seed_content(db_path, "c1", "contract", 1)
        png_data = b"\x89PNG\r\ntest"
        _seed_signature(db_path, "s1", "c1", "dinesh", png_data)
        response = client.get("/signatures/s1/image")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == png_data

    def test_missing_signature_returns_404(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/signatures/nonexistent/image")
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
        )
        sig_id = sig_response.json()["id"]
        sync_response = client.get("/sync")
        changes = sync_response.json()["changes"]
        assert len(changes) == 1
        assert changes[0]["entity_type"] == "signature"
        assert changes[0]["entity_id"] == sig_id
        assert changes[0]["action"] == "create"


class TestSync:
    def test_empty_sync(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/sync")
        assert response.status_code == 200
        assert response.json() == {"changes": []}

    def test_sync_with_since_filter(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.get("/sync?since=2099-01-01T00:00:00Z")
        assert response.status_code == 200
        assert response.json() == {"changes": []}


class TestDeviceTokens:
    def test_register_token(self, app_client: tuple[TestClient, Path]) -> None:
        client, _ = app_client
        response = client.post(
            "/device-tokens",
            json={"signer": "dinesh", "token": "abc123"},
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
        )
        response = client.post(
            "/device-tokens",
            json={"signer": "carolina", "token": "abc123"},
        )
        assert response.status_code == 201
        assert response.json()["signer"] == "carolina"


class TestErrorEnvelope:
    def test_404_uses_standard_envelope(
        self, app_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = app_client
        response = client.get("/content/missing")
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
