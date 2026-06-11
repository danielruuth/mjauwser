from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Owner
from schemas import OwnerCreate, OwnerUpdate, OwnerResponse

router = APIRouter(prefix="/api/owners", tags=["owners"])


@router.get("", response_model=list[OwnerResponse])
async def list_owners(q: str | None = None, session: AsyncSession = Depends(get_session)):
    query = select(Owner).order_by(Owner.name)
    if q:
        query = query.where(Owner.name.ilike(f"%{q}%"))
    result = await session.execute(query)
    return result.scalars().all()


@router.post("", response_model=OwnerResponse, status_code=201)
async def create_owner(body: OwnerCreate, session: AsyncSession = Depends(get_session)):
    owner = Owner(name=body.name, phone=body.phone, email=body.email)
    session.add(owner)
    await session.commit()
    await session.refresh(owner)
    return owner


@router.put("/{owner_id}", response_model=OwnerResponse)
async def update_owner(owner_id: int, body: OwnerUpdate, session: AsyncSession = Depends(get_session)):
    owner = await session.get(Owner, owner_id)
    if not owner:
        raise HTTPException(404, "Owner not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(owner, key, value)
    await session.commit()
    await session.refresh(owner)
    return owner


@router.delete("/{owner_id}", status_code=204)
async def delete_owner(owner_id: int, session: AsyncSession = Depends(get_session)):
    owner = await session.get(Owner, owner_id)
    if not owner:
        raise HTTPException(404, "Owner not found")
    await session.delete(owner)
    await session.commit()
