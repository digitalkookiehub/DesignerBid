import logging
import math
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.exceptions import NotFoundError
from app.models.client import Client
from app.models.project import Project, ProjectStatus, Room, RoomType
from app.schemas.project import PaginatedProjectResponse, ProjectCreate, ProjectResponse, ProjectUpdate, RoomCreate, RoomUpdate

logger = logging.getLogger(__name__)


def get_projects(db: Session, user_id: int, page: int = 1, per_page: int = 10, search: str = "", status_filter: str = "", is_admin: bool = False) -> PaginatedProjectResponse:
    query = db.query(Project)
    if not is_admin:
        query = query.filter(Project.user_id == user_id)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    if status_filter:
        query = query.filter(Project.status == ProjectStatus(status_filter))
    total = query.count()
    items = query.options(joinedload(Project.rooms), joinedload(Project.client)).order_by(Project.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    project_responses = []
    for project in items:
        resp = ProjectResponse.model_validate(project)
        resp.client_code = project.client.client_code if project.client else None
        resp.client_name = project.client.name if project.client else None
        project_responses.append(resp)
    return PaginatedProjectResponse(
        items=project_responses, total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


def get_project(db: Session, user_id: int, project_id: int, is_admin: bool = False) -> Project:
    query = db.query(Project).options(joinedload(Project.rooms)).filter(Project.id == project_id)
    if not is_admin:
        query = query.filter(Project.user_id == user_id)
    project = query.first()
    if not project:
        raise NotFoundError("Project")
    return project


def create_project(db: Session, user_id: int, data: ProjectCreate) -> Project:
    client = db.query(Client).filter(Client.id == data.client_id, Client.user_id == user_id).first()
    if not client:
        raise NotFoundError("Client")
    project = Project(
        user_id=user_id,
        client_id=data.client_id,
        name=data.name,
        project_type=data.project_type,
        address=data.address,
        total_area_sqft=Decimal(str(data.total_area_sqft)) if data.total_area_sqft else None,
        budget_min=Decimal(str(data.budget_min)) if data.budget_min else None,
        budget_max=Decimal(str(data.budget_max)) if data.budget_max else None,
        style_preferences=data.style_preferences,
        family_size=data.family_size,
        special_requirements=data.special_requirements,
        notes=data.notes,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info("Project created: %s (id=%d)", project.name, project.id)
    return project


def update_project(db: Session, user_id: int, project_id: int, data: ProjectUpdate, is_admin: bool = False) -> Project:
    project = get_project(db, user_id, project_id, is_admin=is_admin)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("total_area_sqft", "budget_min", "budget_max") and value is not None:
            value = Decimal(str(value))
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    logger.info("Project updated: id=%d", project_id)
    return project


def delete_project(db: Session, user_id: int, project_id: int, is_admin: bool = False) -> None:
    project = get_project(db, user_id, project_id, is_admin=is_admin)
    db.delete(project)
    db.commit()
    logger.info("Project deleted: id=%d", project_id)


def update_status(db: Session, user_id: int, project_id: int, status: str, is_admin: bool = False) -> Project:
    project = get_project(db, user_id, project_id, is_admin=is_admin)
    project.status = ProjectStatus(status)
    db.commit()
    db.refresh(project)
    logger.info("Project status updated: id=%d -> %s", project_id, status)
    return project


# Room management

def add_room(db: Session, user_id: int, project_id: int, data: RoomCreate, is_admin: bool = False) -> Room:
    get_project(db, user_id, project_id, is_admin=is_admin)  # verify ownership
    room = Room(
        project_id=project_id,
        name=data.name,
        room_type=data.room_type,
        length=Decimal(str(data.length)),
        width=Decimal(str(data.width)),
        height=Decimal(str(data.height)),
        carpet_area_sqft=Decimal(str(data.carpet_area_sqft)) if data.carpet_area_sqft else None,
        electrical_points=data.electrical_points,
        plumbing_points=data.plumbing_points,
        windows_count=data.windows_count,
        doors_count=data.doors_count,
        has_false_ceiling=data.has_false_ceiling,
        has_flooring_work=data.has_flooring_work,
        has_painting=data.has_painting,
        has_carpentry=data.has_carpentry,
        notes=data.notes,
        sort_order=data.sort_order,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    logger.info("Room added: %s to project %d", room.name, project_id)
    return room


def get_rooms(db: Session, user_id: int, project_id: int, is_admin: bool = False) -> list[Room]:
    get_project(db, user_id, project_id, is_admin=is_admin)  # verify ownership
    return db.query(Room).filter(Room.project_id == project_id).order_by(Room.sort_order).all()


def update_room(db: Session, user_id: int, project_id: int, room_id: int, data: RoomUpdate, is_admin: bool = False) -> Room:
    get_project(db, user_id, project_id, is_admin=is_admin)  # verify ownership
    room = db.query(Room).filter(Room.id == room_id, Room.project_id == project_id).first()
    if not room:
        raise NotFoundError("Room")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("length", "width", "height", "carpet_area_sqft") and value is not None:
            value = Decimal(str(value))
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    logger.info("Room updated: id=%d", room_id)
    return room


def delete_room(db: Session, user_id: int, project_id: int, room_id: int, is_admin: bool = False) -> None:
    get_project(db, user_id, project_id, is_admin=is_admin)  # verify ownership
    room = db.query(Room).filter(Room.id == room_id, Room.project_id == project_id).first()
    if not room:
        raise NotFoundError("Room")
    db.delete(room)
    db.commit()
    logger.info("Room deleted: id=%d from project %d", room_id, project_id)
