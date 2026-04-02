import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.exceptions import AppException
from app.models.user import User, UserRole
from app.schemas.client import (
    ClientCreate,
    ClientNoteCreate,
    ClientNoteResponse,
    ClientResponse,
    ClientUpdate,
    PaginatedClientResponse,
)
from app.schemas.user import MessageResponse
from app.services import client as client_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=PaginatedClientResponse)
async def list_clients(
    page: int = 1,
    per_page: int = 10,
    search: str = "",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PaginatedClientResponse:
    return client_service.get_clients(db, current_user.id, page, per_page, search, is_admin=current_user.role == UserRole.admin)


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientResponse:
    try:
        client = client_service.create_client(db, current_user.id, data)
        return client
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientResponse:
    try:
        return client_service.get_client(db, current_user.id, client_id, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientResponse:
    try:
        return client_service.update_client(db, current_user.id, client_id, data, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{client_id}", response_model=MessageResponse)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    try:
        client_service.delete_client(db, current_user.id, client_id, is_admin=current_user.role == UserRole.admin)
        return MessageResponse(message="Client deleted")
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{client_id}/notes", response_model=ClientNoteResponse, status_code=201)
async def add_note(
    client_id: int,
    data: ClientNoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientNoteResponse:
    try:
        return client_service.add_note(db, current_user.id, client_id, data.content, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{client_id}/notes", response_model=list[ClientNoteResponse])
async def get_notes(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ClientNoteResponse]:
    try:
        return client_service.get_notes(db, current_user.id, client_id, is_admin=current_user.role == UserRole.admin)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
