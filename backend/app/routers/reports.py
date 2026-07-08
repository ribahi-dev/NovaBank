"""Endpoints de rapports (CdC Module 10) — réservés au Directeur et à l'Admin.

Renvoient un fichier binaire en téléchargement (StreamingResponse) avec le
bon type MIME et un nom de fichier daté.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.services import report_service

router = APIRouter(
    prefix="/reports",
    tags=["Rapports"],
    dependencies=[Depends(require_role("director", "admin"))],
)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


@router.get("/activity.pdf")
def activity_pdf(db: Annotated[Session, Depends(get_db)]):
    """Rapport d'activité de l'agence au format PDF."""
    content = report_service.generate_activity_pdf(db)
    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="novabank_activite_{_stamp()}.pdf"'},
    )


@router.get("/transactions.xlsx")
def transactions_xlsx(db: Annotated[Session, Depends(get_db)]):
    """Export Excel des transactions (avec scores de risque)."""
    content = report_service.generate_transactions_xlsx(db)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="novabank_transactions_{_stamp()}.xlsx"'},
    )
