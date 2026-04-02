import logging
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.project import Project, ProjectStatus
from app.models.quotation import Quotation, QuotationStatus

logger = logging.getLogger(__name__)


def get_stats(db: Session, user_id: int, is_admin: bool = False) -> dict:
    if is_admin:
        total_projects = db.query(func.count(Project.id)).scalar() or 0
        active_projects = db.query(func.count(Project.id)).filter(
            Project.status.in_([ProjectStatus.in_progress, ProjectStatus.design, ProjectStatus.quotation]),
        ).scalar() or 0
        total_clients = db.query(func.count(Client.id)).filter(
            Client.is_active == True  # noqa: E712
        ).scalar() or 0
        quotations_sent = db.query(func.count(Quotation.id)).filter(
            Quotation.status.in_([QuotationStatus.sent, QuotationStatus.approved]),
        ).scalar() or 0
        approved_total = db.query(func.coalesce(func.sum(Quotation.grand_total), 0)).filter(
            Quotation.status == QuotationStatus.approved,
        ).scalar()
        approved_count = db.query(func.count(Quotation.id)).filter(
            Quotation.status == QuotationStatus.approved
        ).scalar() or 0
        rejected_count = db.query(func.count(Quotation.id)).filter(
            Quotation.status == QuotationStatus.rejected
        ).scalar() or 0
    else:
        total_projects = db.query(func.count(Project.id)).filter(Project.user_id == user_id).scalar() or 0
        active_projects = db.query(func.count(Project.id)).filter(
            Project.user_id == user_id,
            Project.status.in_([ProjectStatus.in_progress, ProjectStatus.design, ProjectStatus.quotation]),
        ).scalar() or 0
        total_clients = db.query(func.count(Client.id)).filter(
            Client.user_id == user_id, Client.is_active == True  # noqa: E712
        ).scalar() or 0
        quotations_sent = db.query(func.count(Quotation.id)).join(Project).filter(
            Project.user_id == user_id,
            Quotation.status.in_([QuotationStatus.sent, QuotationStatus.approved]),
        ).scalar() or 0
        approved_total = db.query(func.coalesce(func.sum(Quotation.grand_total), 0)).join(Project).filter(
            Project.user_id == user_id,
            Quotation.status == QuotationStatus.approved,
        ).scalar()
        approved_count = db.query(func.count(Quotation.id)).join(Project).filter(
            Project.user_id == user_id, Quotation.status == QuotationStatus.approved
        ).scalar() or 0
        rejected_count = db.query(func.count(Quotation.id)).join(Project).filter(
            Project.user_id == user_id, Quotation.status == QuotationStatus.rejected
        ).scalar() or 0

    decisions = approved_count + rejected_count
    approval_rate = round((approved_count / decisions * 100), 1) if decisions > 0 else 0.0

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_clients": total_clients,
        "quotations_sent": quotations_sent,
        "total_revenue": float(approved_total or 0),
        "approval_rate": approval_rate,
    }
