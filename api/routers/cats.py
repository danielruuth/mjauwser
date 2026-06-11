from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Cat, Owner, Breed, CatShowDay, ShowDay, Ring, RingQueue
from schemas import CatCreate, CatUpdate, CatResponse, CatShowDayUpdate, CatShowDayStatusUpdate, CatShowDayResponse, CatWithDaysResponse, OwnerResponse
from ws.events import CAT_CREATED, CAT_UPDATED, CAT_DELETED, CAT_STATUS_UPDATED, DAY_CAT_STATUS_CHANGED
from ws.manager import manager

router = APIRouter(prefix="/api/cats", tags=["cats"])


def _cat_to_response(cat: Cat) -> CatResponse:
    return CatResponse(
        id=cat.id,
        name=cat.name,
        breed_ems=cat.breed_ems,
        breed_name=cat.breed_rel.name if cat.breed_rel else "",
        gender=cat.gender,
        show_class=cat.show_class,
        birth_date=cat.birth_date,
        registration_nr=cat.registration_nr,
        owner=OwnerResponse.model_validate(cat.owner_rel) if cat.owner_rel else None,
        status=cat.status,
    )


async def _resolve_breed(session: AsyncSession, breed_ems: str) -> Breed:
    breed = await session.execute(select(Breed).where(Breed.breed_code == breed_ems))
    breed = breed.scalar_one_or_none()
    if not breed:
        raise HTTPException(400, f"Unknown breed_ems '{breed_ems}'")
    return breed


async def _resolve_owner(session: AsyncSession, owner_id: int | None = None, owner_name: str | None = None) -> int | None:
    if owner_id is not None:
        owner = await session.get(Owner, owner_id)
        if not owner:
            raise HTTPException(404, f"Owner with id {owner_id} not found")
        return owner.id
    if owner_name:
        result = await session.execute(select(Owner).where(Owner.name == owner_name))
        owner = result.scalar_one_or_none()
        if not owner:
            owner = Owner(name=owner_name)
            session.add(owner)
            await session.flush()
        return owner.id
    return None


@router.get("", response_model=list[CatResponse])
async def list_cats(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Cat).order_by(Cat.id).options(selectinload(Cat.breed_rel), selectinload(Cat.owner_rel))
    )
    return [_cat_to_response(c) for c in result.scalars().all()]


@router.get("/{cat_id}", response_model=CatWithDaysResponse)
async def get_cat(cat_id: int, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Cat, cat_id, options=[selectinload(Cat.breed_rel), selectinload(Cat.owner_rel), selectinload(Cat.days).selectinload(CatShowDay.day)])
    if not cat:
        raise HTTPException(404, "Cat not found")
    return cat_with_days(cat)


@router.post("", response_model=CatResponse, status_code=201)
async def create_cat(body: CatCreate, session: AsyncSession = Depends(get_session)):
    await _resolve_breed(session, body.breed_ems)
    owner_id = await _resolve_owner(session, owner_id=body.owner_id, owner_name=body.owner_name)
    cat = Cat(
        name=body.name,
        breed_ems=body.breed_ems,
        gender=body.gender,
        show_class=body.show_class,
        birth_date=body.birth_date,
        registration_nr=body.registration_nr,
        owner_id=owner_id,
        status=body.status,
    )
    session.add(cat)
    await session.commit()
    await session.refresh(cat, ["breed_rel", "owner_rel"])
    resp = _cat_to_response(cat)
    await manager.broadcast(CAT_CREATED, {"cat": resp.model_dump()})
    return resp


@router.put("/{cat_id}", response_model=CatResponse)
async def update_cat(cat_id: int, body: CatUpdate, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Cat, cat_id, options=[selectinload(Cat.breed_rel), selectinload(Cat.owner_rel)])
    if not cat:
        raise HTTPException(404, "Cat not found")
    update_data = body.model_dump(exclude_unset=True)
    if "breed_ems" in update_data and update_data["breed_ems"] is not None:
        await _resolve_breed(session, update_data["breed_ems"])
    if "owner_name" in update_data or "owner_id" in update_data:
        owner_id = await _resolve_owner(
            session,
            owner_id=update_data.get("owner_id"),
            owner_name=update_data.get("owner_name"),
        )
        cat.owner_id = owner_id
        update_data.pop("owner_name", None)
        update_data.pop("owner_id", None)
    for key, value in update_data.items():
        setattr(cat, key, value)
    await session.commit()
    await session.refresh(cat, ["breed_rel", "owner_rel"])
    resp = _cat_to_response(cat)
    await manager.broadcast(CAT_UPDATED, {"cat": resp.model_dump()})
    return resp


@router.patch("/{cat_id}/status", response_model=CatResponse)
async def update_cat_status(cat_id: int, status: str, session: AsyncSession = Depends(get_session)):
    if status not in ("present", "absent", "judged"):
        raise HTTPException(400, "Invalid status. Must be present, absent, or judged")
    cat = await session.get(Cat, cat_id, options=[selectinload(Cat.breed_rel), selectinload(Cat.owner_rel)])
    if not cat:
        raise HTTPException(404, "Cat not found")
    cat.status = status
    await session.commit()
    await session.refresh(cat, ["breed_rel"])
    resp = _cat_to_response(cat)
    await manager.broadcast(CAT_STATUS_UPDATED, {"cat": resp.model_dump()})
    return resp


@router.delete("/{cat_id}", status_code=204)
async def delete_cat(cat_id: int, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Cat, cat_id)
    if not cat:
        raise HTTPException(404, "Cat not found")
    await session.delete(cat)
    await session.commit()
    await manager.broadcast(CAT_DELETED, {"cat_id": cat_id})


# ── Cat show-day assignments ──

@router.get("/{cat_id}/days", response_model=list[CatShowDayResponse])
async def list_cat_days(cat_id: int, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Cat, cat_id)
    if not cat:
        raise HTTPException(404, "Cat not found")
    result = await session.execute(
        select(CatShowDay).where(CatShowDay.cat_id == cat_id).options(
            selectinload(CatShowDay.day)
        )
    )
    return [
        CatShowDayResponse(
            cat_id=csd.cat_id,
            show_day_id=csd.show_day_id,
            catalog_nr=csd.catalog_nr,
            day_name=csd.day.name if csd.day else "",
            status=csd.status,
        )
        for csd in result.scalars().all()
    ]


@router.put("/{cat_id}/days/{day_id}", response_model=CatShowDayResponse)
async def update_cat_day(cat_id: int, day_id: int, body: CatShowDayUpdate, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Cat, cat_id)
    if not cat:
        raise HTTPException(404, "Cat not found")
    day = await session.get(ShowDay, day_id)
    if not day:
        raise HTTPException(404, "Day not found")

    result = await session.execute(
        select(CatShowDay).where(CatShowDay.cat_id == cat_id, CatShowDay.show_day_id == day_id)
    )
    csd = result.scalar_one_or_none()
    if csd:
        csd.catalog_nr = body.catalog_nr
    else:
        csd = CatShowDay(cat_id=cat_id, show_day_id=day_id, catalog_nr=body.catalog_nr)
        session.add(csd)

    await session.commit()
    await session.refresh(csd)
    return CatShowDayResponse(
        cat_id=csd.cat_id,
        show_day_id=csd.show_day_id,
        catalog_nr=csd.catalog_nr,
        day_name=day.name,
        status=csd.status,
    )


@router.delete("/{cat_id}/days/{day_id}", status_code=204)
async def delete_cat_day(cat_id: int, day_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(CatShowDay).where(CatShowDay.cat_id == cat_id, CatShowDay.show_day_id == day_id)
    )
    csd = result.scalar_one_or_none()
    if not csd:
        raise HTTPException(404, "Cat-day entry not found")
    await session.delete(csd)
    await session.commit()


@router.patch("/{cat_id}/days/{day_id}/status", response_model=CatShowDayResponse)
async def update_cat_day_status(cat_id: int, day_id: int, body: CatShowDayStatusUpdate, session: AsyncSession = Depends(get_session)):
    if body.status not in ("unchecked", "present", "absent", "judged"):
        raise HTTPException(400, "Invalid status. Must be unchecked, present, absent, or judged")

    result = await session.execute(
        select(CatShowDay).where(CatShowDay.cat_id == cat_id, CatShowDay.show_day_id == day_id)
    )
    csd = result.scalar_one_or_none()
    if not csd:
        raise HTTPException(404, "Cat-day entry not found")

    csd.status = body.status

    if body.status == "absent":
        day_rings = await session.execute(select(Ring).where(Ring.show_day_id == day_id))
        ring_ids = [r.id for r in day_rings.scalars().all()]
        if ring_ids:
            await session.execute(
                sa_delete(RingQueue).where(
                    RingQueue.ring_id.in_(ring_ids),
                    RingQueue.cat_id == cat_id,
                )
            )

    await session.commit()
    await session.refresh(csd)

    day = await session.get(ShowDay, day_id)
    cat = await session.get(Cat, cat_id)

    resp = CatShowDayResponse(
        cat_id=csd.cat_id,
        show_day_id=csd.show_day_id,
        catalog_nr=csd.catalog_nr,
        day_name=day.name if day else "",
        status=csd.status,
    )

    await manager.broadcast(DAY_CAT_STATUS_CHANGED, {
        "cat_id": cat_id,
        "show_day_id": day_id,
        "status": body.status,
        "catalog_nr": csd.catalog_nr,
        "cat_name": cat.name if cat else "",
    })

    return resp


def cat_with_days(cat: Cat) -> CatWithDaysResponse:
    return CatWithDaysResponse(
        id=cat.id,
        name=cat.name,
        breed_ems=cat.breed_ems,
        breed_name=cat.breed_rel.name if cat.breed_rel else "",
        gender=cat.gender,
        show_class=cat.show_class,
        birth_date=cat.birth_date,
        registration_nr=cat.registration_nr,
        owner=OwnerResponse.model_validate(cat.owner_rel) if cat.owner_rel else None,
        status=cat.status,
        days=[
            CatShowDayResponse(
                cat_id=d.cat_id,
                show_day_id=d.show_day_id,
                catalog_nr=d.catalog_nr,
                day_name=d.day.name if d.day else "",
                status=d.status,
            )
            for d in cat.days
        ],
    )
