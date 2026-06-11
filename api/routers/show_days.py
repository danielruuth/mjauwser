from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Show, ShowDay, Ring, Judge, Category, RingCategory, Cat, CatShowDay, RingQueue
from schemas import (
    ShowDayCreate, ShowDayUpdate, ShowDayResponse, ShowDayFullResponse,
    RingCreate, RingResponse, RingUpdate, RingQueueCreate, RingQueueResponse,
    RingQueueItemResponse, CatResponse, PauseRequest,
    JudgeResponse, CategoryResponse,
)
from ws.events import (
    DAY_CREATED, DAY_UPDATED, DAY_DELETED,
    RING_CREATED, RING_UPDATED, RING_DELETED,
    RING_PROGRESSED, RING_STATUS_CHANGED, RING_JUDGE_ASSIGNED, RING_CATEGORIES_UPDATED,
    QUEUE_ITEM_ADDED, QUEUE_ITEM_REMOVED,
)
from ws.manager import manager
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["show_days"])

# ── Helper schemas ──

class JudgeAssignment(BaseModel):
    judge_id: Optional[int] = None

class CategoryAssignment(BaseModel):
    category_ids: list[int] = []


def _ring_to_response(ring: Ring) -> RingResponse:
    judge = None
    if ring.judge_rel:
        judge = JudgeResponse(
            id=ring.judge_rel.id,
            name=ring.judge_rel.name,
            photo=ring.judge_rel.photo,
            bio=ring.judge_rel.bio,
            flag=ring.judge_rel.flag,
            categories=[CategoryResponse.model_validate(c) for c in ring.judge_rel.categories],
        )
    return RingResponse(
        id=ring.id,
        show_day_id=ring.show_day_id,
        ring_number=ring.ring_number,
        judge=judge,
        status=ring.status,
        current_catalog_nr=ring.current_catalog_nr,
        current_class=ring.current_class,
        pause_message=ring.pause_message,
        categories=[CategoryResponse.model_validate(rc.category) for rc in ring.categories if rc.category],
    )


async def _load_ring(ring_id: int, session: AsyncSession) -> Ring | None:
    result = await session.execute(
        select(Ring).where(Ring.id == ring_id).options(
            selectinload(Ring.categories),
            selectinload(Ring.judge_rel).selectinload(Judge.categories),
        )
    )
    return result.scalar_one_or_none()


# ── Day endpoints ──

@router.get("/shows/{show_id}/days", response_model=list[ShowDayResponse])
async def list_days(show_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ShowDay).where(ShowDay.show_id == show_id).order_by(ShowDay.sort_order)
    )
    return result.scalars().all()


@router.get("/days/{day_id}", response_model=ShowDayFullResponse)
async def get_day(day_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ShowDay).where(ShowDay.id == day_id).options(
            selectinload(ShowDay.rings).selectinload(Ring.categories),
            selectinload(ShowDay.rings).selectinload(Ring.judge_rel).selectinload(Judge.categories),
        )
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(404, "Day not found")
    return ShowDayFullResponse(
        id=day.id,
        show_id=day.show_id,
        name=day.name,
        sort_order=day.sort_order,
        rings=[_ring_to_response(r) for r in day.rings],
    )


@router.post("/shows/{show_id}/days", response_model=ShowDayResponse, status_code=201)
async def create_day(show_id: int, body: ShowDayCreate, session: AsyncSession = Depends(get_session)):
    show = await session.get(Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    day = ShowDay(show_id=show_id, name=body.name, sort_order=body.sort_order)
    session.add(day)
    await session.commit()
    await session.refresh(day)
    await manager.broadcast(DAY_CREATED, {"day": ShowDayResponse.model_validate(day).model_dump()})
    return day


@router.put("/days/{day_id}", response_model=ShowDayResponse)
async def update_day(day_id: int, body: ShowDayUpdate, session: AsyncSession = Depends(get_session)):
    day = await session.get(ShowDay, day_id)
    if not day:
        raise HTTPException(404, "Day not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(day, key, value)
    await session.commit()
    await session.refresh(day)
    await manager.broadcast(DAY_UPDATED, {"day": ShowDayResponse.model_validate(day).model_dump()})
    return day


@router.delete("/days/{day_id}", status_code=204)
async def delete_day(day_id: int, session: AsyncSession = Depends(get_session)):
    day = await session.get(ShowDay, day_id)
    if not day:
        raise HTTPException(404, "Day not found")
    await session.delete(day)
    await session.commit()
    await manager.broadcast(DAY_DELETED, {"day_id": day_id})


# ── Ring endpoints ──

@router.get("/days/{day_id}/rings", response_model=list[RingResponse])
async def list_rings(day_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Ring).where(Ring.show_day_id == day_id).order_by(Ring.ring_number).options(
            selectinload(Ring.categories),
            selectinload(Ring.judge_rel).selectinload(Judge.categories),
        )
    )
    return [_ring_to_response(r) for r in result.scalars().all()]


@router.post("/days/{day_id}/rings", response_model=RingResponse, status_code=201)
async def create_ring(day_id: int, body: RingCreate, session: AsyncSession = Depends(get_session)):
    day = await session.get(ShowDay, day_id)
    if not day:
        raise HTTPException(404, "Day not found")

    existing = await session.execute(
        select(Ring).where(Ring.show_day_id == day_id, Ring.ring_number == body.ring_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Ring number already exists in this day")

    ring = Ring(show_day_id=day_id, ring_number=body.ring_number)

    category_ids = list(body.category_ids)
    if body.judge_id:
        judge = await session.get(Judge, body.judge_id, options=[selectinload(Judge.categories)])
        if not judge:
            raise HTTPException(404, "Judge not found")
        ring.judge_id = body.judge_id
        if not category_ids:
            category_ids = [c.id for c in judge.categories]

    session.add(ring)
    await session.flush()

    for cat_id in category_ids:
        session.add(RingCategory(ring_id=ring.id, category_id=cat_id))

    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_CREATED, {"ring": resp.model_dump()})
    return resp


@router.get("/rings/{ring_id}", response_model=RingResponse)
async def get_ring(ring_id: int, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")
    return _ring_to_response(ring)


@router.put("/rings/{ring_id}", response_model=RingResponse)
async def update_ring(ring_id: int, body: RingUpdate, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(ring, key, value)
    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_UPDATED, {"ring": resp.model_dump()})
    return resp


@router.put("/rings/{ring_id}/categories", response_model=RingResponse)
async def update_ring_categories(ring_id: int, body: CategoryAssignment, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")

    await session.execute(sa_delete(RingCategory).where(RingCategory.ring_id == ring_id))
    for cat_id in body.category_ids:
        session.add(RingCategory(ring_id=ring.id, category_id=cat_id))

    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_CATEGORIES_UPDATED, {"ring": resp.model_dump()})
    return resp


@router.delete("/rings/{ring_id}", status_code=204)
async def delete_ring(ring_id: int, session: AsyncSession = Depends(get_session)):
    ring = await session.get(Ring, ring_id)
    if not ring:
        raise HTTPException(404, "Ring not found")
    await session.delete(ring)
    await session.commit()
    await manager.broadcast(RING_DELETED, {"ring_id": ring_id})


@router.post("/rings/{ring_id}/next-cat", response_model=RingResponse)
async def next_cat(ring_id: int, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")
    if ring.status == "paused":
        raise HTTPException(400, "Ring is paused")

    # Mark current ongoing entry as completed
    await session.execute(
        update(RingQueue).where(
            RingQueue.ring_id == ring_id,
            RingQueue.status == "ongoing",
        ).values(status="completed")
    )

    # Find next pending queue entry
    next_q = await session.execute(
        select(RingQueue).where(
            RingQueue.ring_id == ring_id,
            RingQueue.status == "pending",
        ).order_by(RingQueue.sequence_order).limit(1)
    )
    next_entry = next_q.scalar_one_or_none()
    if not next_entry:
        raise HTTPException(400, "No more cats in queue")

    cat = await session.get(Cat, next_entry.cat_id)
    if cat:
        csd_result = await session.execute(
            select(CatShowDay).where(
                CatShowDay.cat_id == cat.id,
                CatShowDay.show_day_id == ring.show_day_id,
            )
        )
        csd = csd_result.scalar_one_or_none()
        if csd:
            ring.current_catalog_nr = csd.catalog_nr
        ring.current_class = cat.show_class
        next_entry.status = "ongoing"

    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_PROGRESSED, {"ring": resp.model_dump()})
    return resp


@router.post("/rings/{ring_id}/previous-cat", response_model=RingResponse)
async def previous_cat(ring_id: int, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")
    if ring.status == "paused":
        raise HTTPException(400, "Ring is paused")

    # Find current ongoing entry (highest seq first if multiple somehow exist)
    current_q = await session.execute(
        select(RingQueue).where(
            RingQueue.ring_id == ring_id,
            RingQueue.status == "ongoing",
        ).order_by(RingQueue.sequence_order.desc()).limit(1)
    )
    current_entry = current_q.scalar_one_or_none()
    if not current_entry:
        raise HTTPException(400, "No ongoing cat to go back from")

    # Find the previous completed entry
    prev_q = await session.execute(
        select(RingQueue).where(
            RingQueue.ring_id == ring_id,
            RingQueue.status == "completed",
            RingQueue.sequence_order < current_entry.sequence_order,
        ).order_by(RingQueue.sequence_order.desc()).limit(1)
    )
    prev_entry = prev_q.scalar_one_or_none()
    if not prev_entry:
        raise HTTPException(400, "No previous cat to go back to")

    # Revert current entry back to pending
    current_entry.status = "pending"

    # Set previous entry back to ongoing
    prev_entry.status = "ongoing"

    # Update ring state from previous cat
    cat = await session.get(Cat, prev_entry.cat_id)
    if cat:
        csd_result = await session.execute(
            select(CatShowDay).where(
                CatShowDay.cat_id == cat.id,
                CatShowDay.show_day_id == ring.show_day_id,
            )
        )
        csd = csd_result.scalar_one_or_none()
        if csd:
            ring.current_catalog_nr = csd.catalog_nr
        ring.current_class = cat.show_class

    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_PROGRESSED, {"ring": resp.model_dump()})
    return resp


@router.post("/rings/{ring_id}/pause", response_model=RingResponse)
async def pause_ring(ring_id: int, body: PauseRequest | None = None, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")
    ring.status = "paused"
    ring.pause_message = body.pause_message if body else None
    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_STATUS_CHANGED, {"ring": resp.model_dump()})
    return resp


@router.post("/rings/{ring_id}/resume", response_model=RingResponse)
async def resume_ring(ring_id: int, session: AsyncSession = Depends(get_session)):
    ring = await _load_ring(ring_id, session)
    if not ring:
        raise HTTPException(404, "Ring not found")
    ring.status = "active"
    ring.pause_message = None
    await session.commit()
    await session.refresh(ring, ["categories", "judge_rel"])
    resp = _ring_to_response(ring)
    await manager.broadcast(RING_STATUS_CHANGED, {"ring": resp.model_dump()})
    return resp


# ── Queue endpoints ──

@router.get("/rings/{ring_id}/queue", response_model=list[RingQueueItemResponse])
async def list_ring_queue(ring_id: int, session: AsyncSession = Depends(get_session)):
    ring = await session.get(Ring, ring_id)
    if not ring:
        raise HTTPException(404, "Ring not found")
    result = await session.execute(
        select(RingQueue)
        .where(RingQueue.ring_id == ring_id)
        .order_by(RingQueue.sequence_order)
        .options(selectinload(RingQueue.cat).selectinload(Cat.breed_rel))
    )
    entries = list(result.scalars().all())
    catalog_map: dict[int, int] = {}
    if ring.show_day_id and entries:
        csd_result = await session.execute(
            select(CatShowDay).where(
                CatShowDay.show_day_id == ring.show_day_id,
                CatShowDay.cat_id.in_([e.cat_id for e in entries]),
            )
        )
        catalog_map = {csd.cat_id: csd.catalog_nr for csd in csd_result.scalars().all()}
    return [
        RingQueueItemResponse(
            id=e.id,
            ring_id=e.ring_id,
            cat_id=e.cat_id,
            sequence_order=e.sequence_order,
            status=e.status,
            catalog_nr=catalog_map.get(e.cat_id),
            cat=CatResponse.model_validate(e.cat) if e.cat else None,
        )
        for e in entries
    ]


@router.post("/rings/{ring_id}/queue", response_model=RingQueueResponse, status_code=201)
async def add_to_ring_queue(ring_id: int, body: RingQueueCreate, session: AsyncSession = Depends(get_session)):
    ring = await session.get(Ring, ring_id)
    if not ring:
        raise HTTPException(404, "Ring not found")
    cat = await session.get(Cat, body.cat_id)
    if not cat:
        raise HTTPException(404, "Cat not found")

    existing = await session.execute(
        select(RingQueue).where(
            RingQueue.ring_id == ring_id,
            RingQueue.sequence_order == body.sequence_order,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Sequence order already exists for this ring")

    entry = RingQueue(ring_id=ring_id, cat_id=body.cat_id, sequence_order=body.sequence_order)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    await manager.broadcast(QUEUE_ITEM_ADDED, {"queue_item": RingQueueResponse.model_validate(entry).model_dump()})
    return entry


@router.delete("/queue/{queue_id}", status_code=204)
async def remove_from_ring_queue(queue_id: int, session: AsyncSession = Depends(get_session)):
    entry = await session.get(RingQueue, queue_id)
    if not entry:
        raise HTTPException(404, "Queue entry not found")
    await session.delete(entry)
    await session.commit()
    await manager.broadcast(QUEUE_ITEM_REMOVED, {"queue_id": queue_id})
