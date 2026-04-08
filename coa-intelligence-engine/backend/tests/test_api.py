"""
API endpoint tests using FastAPI TestClient.
These test routing, request validation, and error shapes.
Supabase and storage are mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import io


# Patch Supabase and storage before importing app
@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "test-uuid-1234",
            "original_filename": "test.pdf",
            "file_path": "",
            "file_size_bytes": 1024,
            "mime_type": "application/pdf",
            "status": "pending",
            "pages_processed": 0,
            "created_at": "2026-04-08T10:00:00Z",
            "updated_at": "2026-04-08T10:00:00Z",
        }
    ]
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    mock_client.storage.from_.return_value.upload.return_value = {}

    with patch("app.db.client._supabase_client", mock_client):
        with patch("app.db.client.get_client", return_value=mock_client):
            yield mock_client


@pytest.fixture
def client():
    # Patch settings to avoid requiring real env vars
    with patch("app.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.anthropic_api_key = "test-key"
        settings.gemini_api_key = "test-key"
        settings.supabase_url = "https://test.supabase.co"
        settings.supabase_service_key = "test-key"
        settings.max_file_size_mb = 50
        settings.extraction_confidence_threshold = 0.6
        settings.extraction_warning_band_percent = 5.0
        settings.allowed_origins = ["http://localhost:3000"]
        settings.coa_storage_bucket = "coa-uploads"
        settings.claude_model = "claude-opus-4-6"
        settings.gemini_model = "gemini-1.5-flash"
        settings.log_level = "INFO"
        settings.environment = "test"
        mock_settings.return_value = settings

        with patch("app.db.client.init_supabase", new_callable=AsyncMock):
            from app.main import app
            return TestClient(app, raise_server_exceptions=False)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_upload_no_file(client):
    response = client.post("/api/coa/upload")
    assert response.status_code == 422


def test_upload_unsupported_file_type(client):
    with patch("app.api.routes.coa.upload_coa_file", new_callable=AsyncMock) as mock_upload:
        with patch("app.db.queries.create_submission", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": "test-uuid-1234"}
            mock_upload.return_value = "test-uuid-1234/test.txt"

            response = client.post(
                "/api/coa/upload",
                files={"file": ("test.txt", b"plain text content", "text/plain")},
            )
            assert response.status_code == 422


def test_status_not_found(client):
    with patch("app.db.queries.get_submission", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get("/api/coa/status/nonexistent-id")
        assert response.status_code == 404
        body = response.json()
        assert body["detail"]["error"]["code"] == "NOT_FOUND"


def test_status_found(client):
    with patch("app.db.queries.get_submission", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {
            "id": "test-uuid-1234",
            "status": "processing",
            "page_count": 3,
            "pages_processed": 1,
            "error_message": None,
        }
        response = client.get("/api/coa/status/test-uuid-1234")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "processing"
        assert data["page_count"] == 3


def test_result_not_found(client):
    with patch("app.db.queries.get_submission", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get("/api/coa/result/nonexistent-id")
        assert response.status_code == 404


def test_result_not_ready(client):
    with patch("app.db.queries.get_submission", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "test-uuid-1234", "status": "processing"}
        response = client.get("/api/coa/result/test-uuid-1234")
        assert response.status_code == 409
        body = response.json()
        assert body["detail"]["error"]["code"] == "NOT_READY"


def test_export_invalid_format(client):
    with patch("app.db.queries.get_submission", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "test-uuid-1234", "status": "completed"}
        response = client.get("/api/coa/export/test-uuid-1234?format=xlsx")
        assert response.status_code == 422


def test_submissions_list(client):
    with patch("app.db.queries.list_recent_submissions", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {"id": "abc", "original_filename": "test.pdf", "status": "completed", "created_at": "2026-04-08T10:00:00Z"}
        ]
        response = client.get("/api/coa/submissions")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == "abc"


def test_seed_specs_missing_fields(client):
    response = client.post("/api/specs/parameters", json={})
    assert response.status_code == 422


def test_seed_specs_valid(client):
    with patch("app.db.queries.upsert_product", new_callable=AsyncMock) as mock_product:
        with patch("app.db.queries.upsert_spec_table", new_callable=AsyncMock) as mock_table:
            with patch("app.db.queries.insert_spec_parameters", new_callable=AsyncMock) as mock_params:
                mock_product.return_value = {"id": "prod-123"}
                mock_table.return_value = {"id": "spec-456"}
                mock_params.return_value = [{"id": "param-1"}, {"id": "param-2"}]

                response = client.post(
                    "/api/specs/parameters",
                    json={
                        "product_name": "Paracetamol IP",
                        "product_grade": "IP",
                        "parameters": [
                            {
                                "parameter_name": "Assay",
                                "specification_limit": "98.0 - 102.0%",
                                "is_quantitative": True,
                            },
                            {
                                "parameter_name": "Description",
                                "specification_limit": "White crystalline powder",
                                "is_quantitative": False,
                            },
                        ],
                    },
                )
                assert response.status_code == 201
                data = response.json()["data"]
                assert data["parameters_inserted"] == 2
