import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.exceptions import AppException
from app.models.user import User, UserRole
from app.schemas.project import (
    PaginatedProjectResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectStatusUpdate,
    ProjectUpdate,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from app.schemas.user import MessageResponse
from app.services import project as project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=PaginatedProjectResponse)
async def list_projects(
    page: int = 1, per_page: int = 10, search: str = "", status: str = "",
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    return project_service.get_projects(db, current_user.id, page, per_page, search, status, is_admin=current_user.role == UserRole.admin)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.create_project(db, current_user.id, data)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.get_project(db, current_user.id, project_id, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int, data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.update_project(db, current_user.id, project_id, data, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        project_service.delete_project(db, current_user.id, project_id, is_admin=current_user.role == UserRole.admin)
        return MessageResponse(message="Project deleted")
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{project_id}/status", response_model=ProjectResponse)
async def update_status(
    project_id: int, data: ProjectStatusUpdate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.update_status(db, current_user.id, project_id, data.status, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Room endpoints

@router.post("/{project_id}/rooms", response_model=RoomResponse, status_code=201)
async def add_room(
    project_id: int, data: RoomCreate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.add_room(db, current_user.id, project_id, data, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{project_id}/rooms", response_model=list[RoomResponse])
async def list_rooms(
    project_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.get_rooms(db, current_user.id, project_id, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{project_id}/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    project_id: int, room_id: int, data: RoomUpdate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        return project_service.update_room(db, current_user.id, project_id, room_id, data, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{project_id}/rooms/{room_id}", response_model=MessageResponse)
async def delete_room(
    project_id: int, room_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    try:
        project_service.delete_room(db, current_user.id, project_id, room_id, is_admin=current_user.role == UserRole.admin)
        return MessageResponse(message="Room deleted")
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
