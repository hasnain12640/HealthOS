import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.core.database import get_db
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import LabReport, Biomarker, HealthProfile, TimelineEvent
from app.services.deterministic.pdf_extractor import extract_text_from_pdf
from app.services.deterministic.biomarker_parser import parse_biomarkers, BIOMARKER_DEFAULTS

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Response schemas ──────────────────────────────────────────────────────────

class BiomarkerOut(BaseModel):
    id: str
    name: str
    value: float
    unit: str
    reference_low: Optional[float]
    reference_high: Optional[float]
    status: str
    category: str

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: str
    profile_id: str
    filename: str
    lab_name: str
    report_date: str
    parsing_method: str
    upload_date: str
    biomarkers: list[BiomarkerOut]

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    id: str
    filename: str
    lab_name: str
    report_date: str
    upload_date: str
    total_biomarkers: int
    abnormal_count: int

    class Config:
        from_attributes = True


# ── Manual entry schema ───────────────────────────────────────────────────────

class ManualBiomarker(BaseModel):
    name: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    category: str = "other"


class ManualReportCreate(BaseModel):
    lab_name: str = "Manual Entry"
    report_date: str
    biomarkers: list[ManualBiomarker] = Field(..., min_length=1)


class CatalogItem(BaseModel):
    name: str
    category: str
    unit: str
    reference_low: Optional[float]
    reference_high: Optional[float]


class CatalogOut(BaseModel):
    biomarkers: list[CatalogItem]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=ReportOut, status_code=201)
async def upload_lab_report(
    lab_name: str = Form(""),
    report_date: str = Form(""),
    file: UploadFile = File(...),
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    profile_id = profile.id

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # Extract text
    try:
        raw_text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from this PDF. Try manual entry instead.",
        )

    report_id = str(uuid.uuid4())
    today = today_iso()

    report = LabReport(
        id=report_id,
        profile_id=profile_id,
        filename=file.filename,
        lab_name=lab_name or _detect_lab_name(raw_text),
        report_date=report_date or _detect_report_date(raw_text) or today,
        raw_text=raw_text,
        parsing_method="pdf_text",
        upload_date=today,
    )
    db.add(report)

    # Parse biomarkers deterministically
    parsed = parse_biomarkers(raw_text, report_id)
    if not parsed:
        # Store the report anyway so the user can see it was uploaded,
        # but return a message that manual entry is needed.
        db.commit()
        raise HTTPException(
            status_code=422,
            detail="Report uploaded but no recognisable biomarkers were extracted. Use manual entry to add results.",
        )

    for b_data in parsed:
        db.add(Biomarker(**b_data))

    db.commit()
    db.refresh(report)

    # Attach biomarkers for response
    report.biomarkers = db.query(Biomarker).filter(Biomarker.report_id == report_id).all()
    return report


@router.post("/manual", response_model=ReportOut, status_code=201)
def create_manual_report(
    data: ManualReportCreate,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    profile_id = profile.id
    from app.services.deterministic.health_calculations import assess_biomarker_status
    report_id = str(uuid.uuid4())
    today = today_iso()

    report = LabReport(
        id=report_id,
        profile_id=profile_id,
        filename=f"manual_entry_{today}.pdf",
        lab_name=data.lab_name,
        report_date=data.report_date,
        raw_text="",
        parsing_method="manual",
        upload_date=today,
    )
    db.add(report)

    for bm in data.biomarkers:
        status = assess_biomarker_status(bm.value, bm.reference_low, bm.reference_high)
        db.add(Biomarker(
            id=str(uuid.uuid4()),
            report_id=report_id,
            name=bm.name,
            value=bm.value,
            unit=bm.unit,
            reference_low=bm.reference_low,
            reference_high=bm.reference_high,
            status=status,
            category=bm.category,
        ))

    db.commit()
    db.refresh(report)
    report.biomarkers = db.query(Biomarker).filter(Biomarker.report_id == report_id).all()

    abnormal_count = sum(1 for b in report.biomarkers if b.status != "normal")
    db.add(TimelineEvent(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=data.report_date,
        event_type="lab",
        title=f"Manual lab report — {data.lab_name}",
        description=(
            f"{len(report.biomarkers)} biomarker(s) added manually. "
            f"{abnormal_count} outside reference range."
        ),
        is_ai_generated=False,
    ))
    db.commit()

    return report


@router.get("/catalog", response_model=CatalogOut)
def get_biomarker_catalog():
    items = [
        CatalogItem(
            name=name,
            category=data["category"],
            unit=data["unit"],
            reference_low=data.get("reference_low"),
            reference_high=data.get("reference_high"),
        )
        for name, data in BIOMARKER_DEFAULTS.items()
    ]
    return CatalogOut(biomarkers=items)


@router.get("", response_model=list[ReportSummary])
def list_reports(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    reports = db.query(LabReport).filter(LabReport.profile_id == profile.id).all()
    result = []
    for r in reports:
        bms = db.query(Biomarker).filter(Biomarker.report_id == r.id).all()
        result.append(ReportSummary(
            id=r.id, filename=r.filename, lab_name=r.lab_name,
            report_date=r.report_date, upload_date=r.upload_date,
            total_biomarkers=len(bms),
            abnormal_count=sum(1 for b in bms if b.status != "normal"),
        ))
    return result


@router.get("/detail/{report_id}", response_model=ReportOut)
def get_report_detail(
    report_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    report = db.query(LabReport).filter(
        LabReport.id == report_id,
        LabReport.profile_id == profile.id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.biomarkers = db.query(Biomarker).filter(Biomarker.report_id == report_id).all()
    return report


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_lab_name(text: str) -> str:
    first_line = text.splitlines()[0].strip() if text.strip() else ""
    known = ["chughtai", "essa", "shaukat khanum", "agha khan", "islamabad diagnostic"]
    for k in known:
        if k in first_line.lower():
            return first_line
    return first_line[:80] if first_line else "Unknown Lab"


def _detect_report_date(text: str) -> Optional[str]:
    import re
    # Matches "15-Aug-2024", "2024-08-15", "15/08/2024"
    patterns = [
        r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None
