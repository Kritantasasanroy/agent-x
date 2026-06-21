"""Analytics + exports (CSV / Excel / PDF) + learning recommendations."""

from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.tracking import TrackingAgent
from app.api.deps import get_current_user
from app.db.models import Application, Job, Setting, User
from app.db.session import get_db
from app.schemas.schemas import Analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=Analytics)
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return TrackingAgent(db).analytics(user_id=user.id)


@router.get("/recommendations")
def recommendations(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    setting = (
        db.query(Setting)
        .filter(Setting.user_id == user.id, Setting.key == "learning_recommendations")
        .one_or_none()
    )
    return json.loads(setting.value) if setting and setting.value else {"recommendations": []}


@router.get("/export")
def export(
    fmt: str = "csv", db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    rows = (
        db.query(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .filter(Application.user_id == user.id)
        .all()
    )
    headers = ["company", "title", "source", "match_score", "status", "submitted_at", "created_at"]
    records = [
        [
            j.company, j.title, j.source, j.match_score,
            str(getattr(a.status, "value", a.status)),
            a.submitted_at.isoformat() if a.submitted_at else "",
            a.created_at.isoformat(),
        ]
        for a, j in rows
    ]

    if fmt == "excel":
        return _excel(headers, records)
    if fmt == "pdf":
        return _pdf(headers, records)
    return _csv(headers, records)


def _csv(headers, records) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(records)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )


def _excel(headers, records) -> StreamingResponse:
    # Minimal SpreadsheetML so we avoid a hard openpyxl dependency.
    rows = "".join(
        "<Row>" + "".join(f'<Cell><Data ss:Type="String">{c}</Data></Cell>' for c in r) + "</Row>"
        for r in [headers, *records]
    )
    xml = (
        '<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" '
        'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Applications">'
        f"<Table>{rows}</Table></Worksheet></Workbook>"
    )
    return StreamingResponse(
        iter([xml]),
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": "attachment; filename=applications.xls"},
    )


def _pdf(headers, records) -> StreamingResponse:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.platypus import SimpleDocTemplate, Table

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER)
    doc.build([Table([headers, *records])])
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=applications.pdf"},
    )
