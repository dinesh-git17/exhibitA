"""Tests for admin session auth, dashboard, CRUD, and APNS integration."""

# pylint: disable=redefined-outer-name,missing-class-docstring,missing-function-docstring,import-outside-toplevel

import os
import sqlite3
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

_TEST_KEY = "test-admin-key-0123456789abcdef"  # gitleaks:allow


def _seed_api_keys(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    key_hash = bcrypt.hashpw(
        _TEST_KEY.encode("utf-8"), bcrypt.gensalt(rounds=4)
    ).decode("utf-8")
    conn.execute(
        "INSERT INTO api_keys (id, signer, key_hash) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), "dinesh", key_hash),
    )
    conn.commit()
    conn.close()


def _seed_content(
    db_path: Path,
    content_id: str,
    content_type: str = "contract",
    section_order: int = 1,
    title: str = "Test",
    body: str = "Test body",
    article_number: str | None = None,
    classification: str | None = None,
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO content "
        "(id, type, title, body, article_number, classification, section_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            content_id,
            content_type,
            title,
            body,
            article_number,
            classification,
            section_order,
        ),
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def admin_client(tmp_path: Path) -> Iterator[tuple[TestClient, Path]]:
    """Create a fresh app with isolated test database for admin tests."""
    db_path = tmp_path / "test.db"
    with patch.dict(os.environ, {"DATABASE_PATH": str(db_path)}):
        from app import create_app

        app = create_app()
        with TestClient(app, base_url="https://testserver") as client:
            _seed_api_keys(db_path)
            yield client, db_path


def _login(client: TestClient) -> TestClient:
    """Perform admin login and return client with session cookie."""
    client.post(
        "/admin/login",
        data={"api_key": _TEST_KEY},
        follow_redirects=False,
    )
    return client


def _sync_log_entries(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT entity_type, entity_id, action FROM sync_log ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _content_rows(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM content ORDER BY section_order").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _session_rows(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM admin_sessions").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Session/Auth Tests ---


class TestAdminAuth:
    def test_unauthenticated_admin_redirects_to_login(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert "/admin/login" in response.headers["location"]

    def test_login_page_renders(self, admin_client: tuple[TestClient, Path]) -> None:
        client, _ = admin_client
        response = client.get("/admin/login")
        assert response.status_code == 200
        assert "API Key" in response.text

    def test_valid_login_creates_session(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        response = client.post(
            "/admin/login",
            data={"api_key": _TEST_KEY},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin/dashboard" in response.headers["location"]

        sessions = _session_rows(db_path)
        assert len(sessions) == 1
        assert sessions[0]["session_id"] is not None
        assert sessions[0]["expires_at"] is not None

    def test_valid_login_sets_session_cookie(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        response = client.post(
            "/admin/login",
            data={"api_key": _TEST_KEY},
            follow_redirects=False,
        )
        cookies = response.cookies
        assert "admin_session" in cookies

    def test_invalid_login_returns_401(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        response = client.post(
            "/admin/login",
            data={"api_key": "wrong-key"},
            follow_redirects=False,
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.text

    def test_invalid_login_no_session_created(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        client.post(
            "/admin/login",
            data={"api_key": "wrong-key"},
            follow_redirects=False,
        )
        sessions = _session_rows(db_path)
        assert len(sessions) == 0

    def test_logout_destroys_session(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _login(client)
        assert len(_session_rows(db_path)) == 1

        client.get("/admin/logout", follow_redirects=False)
        assert len(_session_rows(db_path)) == 0


# --- Dashboard Tests ---


class TestAdminDashboard:
    def test_dashboard_requires_auth(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        response = client.get("/admin/dashboard", follow_redirects=False)
        assert response.status_code == 303
        assert "/admin/login" in response.headers["location"]

    def test_dashboard_renders_counts(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1)
        _seed_content(db_path, "c2", "contract", 2)
        _seed_content(db_path, "l1", "letter", 1)
        _seed_content(db_path, "t1", "thought", 1)
        _seed_content(db_path, "t2", "thought", 2)
        _seed_content(db_path, "t3", "thought", 3)

        _login(client)
        response = client.get("/admin/dashboard")
        assert response.status_code == 200
        html = response.text
        assert "Contracts on file:" in html
        assert "Letters filed:" in html
        assert "Memoranda sealed:" in html
        assert "Signatures executed:" in html

    def test_dashboard_renders_recent_filings(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1, title="Test Contract")

        _login(client)
        response = client.get("/admin/dashboard")
        assert response.status_code == 200
        assert "Test Contract" in response.text

    def test_dashboard_renders_quick_actions(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)
        response = client.get("/admin/dashboard")
        assert "File New Contract" in response.text
        assert "File New Letter" in response.text
        assert "File New Thought" in response.text


# --- Content CRUD Tests ---


class TestAdminContentCreate:
    def test_create_writes_content_and_sync_log(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _login(client)

        with patch("app.routes.admin.send_push", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = []
            response = client.post(
                "/admin/content/create",
                data={
                    "content_type": "thought",
                    "body": "Test thought",
                    "section_order": "1",
                },
                follow_redirects=False,
            )

        assert response.status_code == 303
        content = _content_rows(db_path)
        assert len(content) == 1
        assert content[0]["type"] == "thought"
        assert content[0]["body"] == "Test thought"

        sync = _sync_log_entries(db_path)
        assert len(sync) == 1
        assert sync[0]["entity_type"] == "content"
        assert sync[0]["action"] == "create"

    def test_create_invokes_apns(self, admin_client: tuple[TestClient, Path]) -> None:
        client, _ = admin_client
        _login(client)

        with patch("app.routes.admin.send_push", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = []
            client.post(
                "/admin/content/create",
                data={
                    "content_type": "letter",
                    "title": "Test Letter",
                    "classification": "Sincere",
                    "body": "Dear...",
                    "section_order": "1",
                },
                follow_redirects=False,
            )
            mock_push.assert_called_once()
            call_args = mock_push.call_args
            assert call_args[0][2] == "letter"
            assert call_args[1]["classification"] == "Sincere"

    def test_create_apns_failure_non_blocking(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _login(client)

        with patch("app.routes.admin.send_push", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = ["APNS delivery failed for token abc12345..."]
            response = client.post(
                "/admin/content/create",
                data={
                    "content_type": "thought",
                    "body": "Test",
                    "section_order": "1",
                },
                follow_redirects=False,
            )

        assert response.status_code == 303
        content = _content_rows(db_path)
        assert len(content) == 1


class TestAdminContentUpdate:
    def test_update_writes_sync_log(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1, title="Old", body="Old body")
        _login(client)

        response = client.post(
            "/admin/content/c1/update",
            data={
                "title": "New Title",
                "body": "New body",
                "section_order": "1",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        content = _content_rows(db_path)
        assert content[0]["title"] == "New Title"
        assert content[0]["body"] == "New body"

        sync = _sync_log_entries(db_path)
        assert len(sync) == 1
        assert sync[0]["action"] == "update"

    def test_update_nonexistent_returns_flash_error(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.post(
            "/admin/content/nonexistent/update",
            data={"body": "test", "section_order": "1"},
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestAdminContentReorder:
    def test_reorder_writes_sync_log(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1)
        _login(client)

        response = client.post(
            "/admin/content/c1/reorder",
            data={"section_order": "5"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        content = _content_rows(db_path)
        assert content[0]["section_order"] == 5

        sync = _sync_log_entries(db_path)
        assert len(sync) == 1
        assert sync[0]["action"] == "update"


class TestAdminContentDelete:
    def test_delete_writes_sync_log(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1)
        _login(client)

        response = client.post(
            "/admin/content/c1/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

        content = _content_rows(db_path)
        assert len(content) == 0

        sync = _sync_log_entries(db_path)
        assert len(sync) == 1
        assert sync[0]["action"] == "delete"

    def test_delete_nonexistent_returns_flash_error(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.post(
            "/admin/content/nonexistent/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303


# --- Content List & Form Tests ---


class TestAdminContentList:
    def test_content_list_requires_auth(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        response = client.get("/admin/content", follow_redirects=False)
        assert response.status_code == 303
        assert "/admin/login" in response.headers["location"]

    def test_content_list_renders_grouped_sections(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1, title="Test Contract")
        _seed_content(db_path, "l1", "letter", 1, title="Test Letter")
        _seed_content(db_path, "t1", "thought", 1, title="", body="Test thought body")
        _login(client)

        response = client.get("/admin/content")
        assert response.status_code == 200
        html = response.text
        assert "Contracts" in html
        assert "Letters" in html
        assert "Sealed Thoughts" in html
        assert "Test Contract" in html
        assert "Test Letter" in html
        assert "Test thought body" in html

    def test_content_list_renders_edit_and_delete_actions(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1, title="Contract One")
        _login(client)

        response = client.get("/admin/content")
        html = response.text
        assert "/admin/content/c1/edit" in html
        assert "/admin/content/c1/delete" in html

    def test_content_list_uses_content_row_partial(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1, title="Row Item")
        _login(client)

        response = client.get("/admin/content")
        html = response.text
        assert "Row Item" in html
        assert "Edit" in html
        assert "Delete" in html


class TestAdminContentForm:
    def test_contract_form_renders_required_fields(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.get("/admin/content/new?type=contract")
        assert response.status_code == 200
        html = response.text
        assert 'name="article_number"' in html
        assert 'name="title"' in html
        assert 'name="body"' in html
        assert 'name="requires_signature"' in html
        assert 'name="section_order"' in html

    def test_letter_form_renders_required_fields(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.get("/admin/content/new?type=letter")
        assert response.status_code == 200
        html = response.text
        assert 'name="title"' in html
        assert 'name="subtitle"' in html
        assert 'name="classification"' in html
        assert 'name="body"' in html
        assert 'name="section_order"' in html

    def test_letter_form_has_nine_classifications(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.get("/admin/content/new?type=letter")
        html = response.text
        for cls in [
            "Sincere",
            "Grievance",
            "Motion to Appreciate",
            "Emergency Filing",
            "Brief in Support",
            "Petition for Cuddles",
            "Amicus Brief",
            "Closing Statement",
            "Addendum to Previous Affection",
        ]:
            assert cls in html

    def test_thought_form_renders_minimal_fields(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.get("/admin/content/new?type=thought")
        assert response.status_code == 200
        html = response.text
        assert 'name="body"' in html
        assert 'name="section_order"' in html
        assert "char-count" in html
        assert 'name="title"' not in html

    def test_edit_form_prepopulates_values(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(
            db_path,
            "c1",
            "contract",
            1,
            title="Existing Title",
            body="Existing body",
            article_number="Article I",
        )
        _login(client)

        response = client.get("/admin/content/c1/edit")
        assert response.status_code == 200
        html = response.text
        assert "Existing Title" in html
        assert "Existing body" in html
        assert "Article I" in html

    def test_edit_form_nonexistent_redirects(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.get("/admin/content/nonexistent/edit", follow_redirects=False)
        assert response.status_code == 303

    def test_delete_confirmation_text_present(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 1, title="Delete Me")
        _login(client)

        response = client.get("/admin/content/c1/edit")
        html = response.text
        assert "Delete Filing" in html
        assert "Are you sure, counselor?" in html

    def test_form_requires_auth(self, admin_client: tuple[TestClient, Path]) -> None:
        client, _ = admin_client
        response = client.get(
            "/admin/content/new?type=contract", follow_redirects=False
        )
        assert response.status_code == 303
        assert "/admin/login" in response.headers["location"]

    def test_next_position_prefilled(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, db_path = admin_client
        _seed_content(db_path, "c1", "contract", 3)
        _login(client)

        response = client.get("/admin/content/new?type=contract")
        html = response.text
        assert 'value="4"' in html


class TestAdminContentPreview:
    def test_preview_renders_markdown(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.post(
            "/admin/content/preview",
            data={"body": "**bold** and *italic*"},
        )
        assert response.status_code == 200
        html = response.text
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_preview_renders_paragraphs(
        self, admin_client: tuple[TestClient, Path]
    ) -> None:
        client, _ = admin_client
        _login(client)

        response = client.post(
            "/admin/content/preview",
            data={"body": "First paragraph.\n\nSecond paragraph."},
        )
        assert response.status_code == 200
        html = response.text
        assert "<p>First paragraph.</p>" in html
        assert "<p>Second paragraph.</p>" in html

    def test_preview_requires_auth(self, admin_client: tuple[TestClient, Path]) -> None:
        client, _ = admin_client
        response = client.post(
            "/admin/content/preview",
            data={"body": "test"},
        )
        assert response.status_code == 401

    def test_preview_escapes_html(self, admin_client: tuple[TestClient, Path]) -> None:
        client, _ = admin_client
        _login(client)

        response = client.post(
            "/admin/content/preview",
            data={"body": "<script>alert('xss')</script>"},
        )
        assert response.status_code == 200
        assert "<script>" not in response.text
        assert "&lt;script&gt;" in response.text


# --- APNS Copy Tests ---


class TestApnsCopy:
    def test_contract_copy(self) -> None:
        from app.apns import build_notification_copy

        copy = build_notification_copy("contract", article_number="Article IX")
        assert copy["title"] == "New Filing Received"
        assert "Article IX" in copy["body"]
        assert "signature may be required" in copy["body"]

    def test_letter_copy(self) -> None:
        from app.apns import build_notification_copy

        copy = build_notification_copy("letter", classification="Sincere")
        assert copy["title"] == "Correspondence on Record"
        assert "Sincere" in copy["body"]

    def test_thought_copy(self) -> None:
        from app.apns import build_notification_copy

        copy = build_notification_copy("thought")
        assert copy["title"] == "Classified Memorandum"
        assert "sealed thought" in copy["body"]
