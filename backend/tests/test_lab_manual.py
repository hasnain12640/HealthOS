"""Tests for the manual lab entry flow and biomarker catalog."""
from datetime import date

from tests.conftest import male_headers


def _today() -> str:
    return date.today().isoformat()


def test_get_biomarker_catalog(client, male_headers):
    response = client.get("/api/v1/lab/catalog", headers=male_headers)
    assert response.status_code == 200
    body = response.json()
    assert "biomarkers" in body
    assert len(body["biomarkers"]) > 0

    hemoglobin = next(b for b in body["biomarkers"] if b["name"] == "Hemoglobin")
    assert hemoglobin["category"] == "CBC"
    assert hemoglobin["unit"] == "g/dL"
    assert hemoglobin["reference_low"] == 13.0
    assert hemoglobin["reference_high"] == 17.0


def test_create_manual_report_computes_status_and_timeline_event(client, male_headers):
    payload = {
        "lab_name": "Home Entry",
        "report_date": _today(),
        "biomarkers": [
            {"name": "Hemoglobin", "value": 11.8, "unit": "g/dL", "reference_low": 13.0, "reference_high": 17.0, "category": "CBC"},
            {"name": "TSH", "value": 2.4, "unit": "mIU/L", "reference_low": 0.4, "reference_high": 4.0, "category": "thyroid"},
        ],
    }
    response = client.post("/api/v1/lab/manual", json=payload, headers=male_headers)
    assert response.status_code == 201
    report = response.json()
    assert report["lab_name"] == "Home Entry"
    assert len(report["biomarkers"]) == 2

    statuses = {b["name"]: b["status"] for b in report["biomarkers"]}
    assert statuses["Hemoglobin"] == "low"
    assert statuses["TSH"] == "normal"

    # Report should appear in the list.
    listed = client.get("/api/v1/lab", headers=male_headers).json()
    assert any(r["id"] == report["id"] for r in listed)

    # A timeline event should have been created and surfaced on the dashboard.
    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    lab_events = [e for e in dashboard["timeline"] if e["event_type"] == "lab"]
    assert len(lab_events) >= 1
    assert any("Manual lab report" in e["title"] for e in lab_events)


def test_manual_report_rejects_missing_biomarkers(client, male_headers):
    payload = {"lab_name": "Empty", "report_date": _today(), "biomarkers": []}
    response = client.post("/api/v1/lab/manual", json=payload, headers=male_headers)
    assert response.status_code == 422


def test_pdf_upload_without_biomarkers_persists_with_warning(client, male_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.lab_reports.extract_text_from_pdf",
        lambda _: "Narrative notes with no recognised test results.",
    )
    monkeypatch.setattr(
        "app.api.routes.lab_reports.parse_biomarkers", lambda *_: []
    )

    response = client.post(
        "/api/v1/lab/upload",
        data={"lab_name": "Unrecognised Lab", "report_date": _today()},
        files={"file": ("unrecognised.pdf", b"%PDF-placeholder", "application/pdf")},
        headers=male_headers,
    )

    assert response.status_code == 201
    report = response.json()
    assert report["biomarkers"] == []
    assert "no recognisable biomarkers were extracted" in report["warning"].lower()

    listed = client.get("/api/v1/lab", headers=male_headers).json()
    assert any(item["id"] == report["id"] for item in listed)


def test_pdf_upload_rejects_blank_or_unextractable_text(client, male_headers, monkeypatch):
    monkeypatch.setattr("app.api.routes.lab_reports.extract_text_from_pdf", lambda _: "  ")
    blank_response = client.post(
        "/api/v1/lab/upload",
        files={"file": ("blank.pdf", b"%PDF-placeholder", "application/pdf")},
        headers=male_headers,
    )
    assert blank_response.status_code == 422

    def fail_extraction(_: bytes) -> str:
        raise ValueError("corrupt PDF")

    monkeypatch.setattr("app.api.routes.lab_reports.extract_text_from_pdf", fail_extraction)
    failed_response = client.post(
        "/api/v1/lab/upload",
        files={"file": ("corrupt.pdf", b"%PDF-placeholder", "application/pdf")},
        headers=male_headers,
    )
    assert failed_response.status_code == 422
