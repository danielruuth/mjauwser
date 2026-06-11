from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, defaultload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Show, ShowDay, Cat, CatShowDay, Ring, Judge, Category, Breed, RingQueue, RingCategory, Owner
from schemas import (
    ShowCreate, ShowUpdate, ShowResponse, ShowDetailResponse,
    CatWithDaysResponse, ShowExportData, ShowImportResponse, CatAssignmentProgress,
    ExportCategory, ExportBreed, ExportJudge, ExportCat, ExportCatDayRef,
    ExportDay, ExportRing, ExportQueueEntry, ExportShow,
)
from response_helpers import show_detail_response
from routers.cats import cat_with_days
from ws.events import SHOW_CREATED, SHOW_UPDATED, SHOW_DELETED
from ws.manager import manager


_show_ring_options = [
    selectinload(Show.days)
        .selectinload(ShowDay.rings)
            .selectinload(Ring.judge_rel)
                .selectinload(Judge.categories),
    selectinload(Show.days)
        .selectinload(ShowDay.rings)
            .selectinload(Ring.categories),
]

router = APIRouter(prefix="/api/shows", tags=["shows"])


@router.get("", response_model=list[ShowDetailResponse])
async def list_shows(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Show).order_by(Show.id).options(*_show_ring_options)
    )
    shows = result.scalars().all()
    return [show_detail_response(s) for s in shows]


@router.get("/{show_id}", response_model=ShowDetailResponse)
async def get_show(show_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Show).where(Show.id == show_id).options(*_show_ring_options)
    )
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(404, "Show not found")
    return show_detail_response(show)


@router.post("", response_model=ShowResponse, status_code=201)
async def create_show(body: ShowCreate, session: AsyncSession = Depends(get_session)):
    show = Show(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        status=body.status,
    )
    session.add(show)
    await session.commit()
    await session.refresh(show, ["days"])
    await manager.broadcast(SHOW_CREATED, {"show": ShowResponse.model_validate(show).model_dump()})
    return show


@router.put("/{show_id}", response_model=ShowDetailResponse)
async def update_show(show_id: int, body: ShowUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Show).where(Show.id == show_id).options(*_show_ring_options)
    )
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(404, "Show not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(show, key, value)
    await session.commit()
    result = await session.execute(
        select(Show).where(Show.id == show_id).options(*_show_ring_options)
    )
    show = result.scalar_one_or_none()
    if show:
        await manager.broadcast(SHOW_UPDATED, {"show": ShowResponse.model_validate(show).model_dump()})
    return show_detail_response(show)


@router.delete("/{show_id}", status_code=204)
async def delete_show(show_id: int, session: AsyncSession = Depends(get_session)):
    show = await session.get(Show, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    await session.delete(show)
    await session.commit()
    await manager.broadcast(SHOW_DELETED, {"show_id": show_id})


@router.get("/{show_id}/export")
async def export_show(show_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Show)
        .where(Show.id == show_id)
        .options(
            selectinload(Show.days)
                .selectinload(ShowDay.rings)
                    .selectinload(Ring.judge_rel)
                        .selectinload(Judge.categories),
            selectinload(Show.days)
                .selectinload(ShowDay.rings)
                    .selectinload(Ring.categories),
            selectinload(Show.days)
                .selectinload(ShowDay.rings)
                    .selectinload(Ring.queue_entries),
        )
    )
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(404, "Show not found")

    cat_result = await session.execute(select(Category).order_by(Category.id))
    categories = cat_result.scalars().all()

    breed_result = await session.execute(select(Breed).order_by(Breed.id))
    breeds = breed_result.scalars().all()

    judge_result = await session.execute(
        select(Judge).order_by(Judge.id).options(selectinload(Judge.categories))
    )
    judges = judge_result.scalars().all()

    cat_result = await session.execute(
        select(Cat).order_by(Cat.id).options(selectinload(Cat.days), selectinload(Cat.owner_rel))
    )
    cats = cat_result.scalars().all()

    export_days = []
    for day in (show.days or []):
        export_rings = []
        for ring in (day.rings or []):
            export_rings.append(ExportRing(
                id=ring.id,
                ring_number=ring.ring_number,
                judge_id=ring.judge_rel.id if ring.judge_rel else None,
                category_ids=[rc.category_id for rc in (ring.categories or [])],
                queue=[ExportQueueEntry(
                    cat_id=q.cat_id,
                    sequence_order=q.sequence_order,
                    status=q.status,
                ) for q in (ring.queue_entries or [])],
            ))
        export_days.append(ExportDay(
            id=day.id,
            name=day.name,
            sort_order=day.sort_order,
            rings=export_rings,
        ))

    return ShowExportData(
        version=1,
        exported_at=datetime.utcnow().isoformat() + "Z",
        categories=[ExportCategory(id=c.id, name=c.name, description=c.description) for c in categories],
        breeds=[ExportBreed(id=b.id, breed_code=b.breed_code, name=b.name, category_id=b.category_id) for b in breeds],
        judges=[ExportJudge(
            id=j.id, name=j.name, flag=j.flag,
            category_ids=[c.id for c in (j.categories or [])],
        ) for j in judges],
        cats=[ExportCat(
            id=c.id, name=c.name, breed_ems=c.breed_ems,
            gender=c.gender, show_class=c.show_class,
            birth_date=c.birth_date, registration_nr=c.registration_nr,
            owner=c.owner_rel.name if c.owner_rel else None,
            owner_id=c.owner_id, status=c.status,
            days=[ExportCatDayRef(show_day_id=cd.show_day_id, catalog_nr=cd.catalog_nr) for cd in (c.days or [])],
        ) for c in cats],
        show=ExportShow(
            name=show.name, start_date=show.start_date,
            end_date=show.end_date, status=show.status,
            days=export_days,
        ),
    )


@router.post("/import", response_model=ShowImportResponse, status_code=201)
async def import_show(data: ShowExportData, session: AsyncSession = Depends(get_session)):
    old_category: dict[int, Category] = {}
    old_breed: dict[int, Breed] = {}
    old_judge: dict[int, Judge] = {}
    old_cat: dict[int, Cat] = {}
    old_day: dict[int, ShowDay] = {}

    try:
        # 1. Categories — find-or-create by name
        categories_found = 0
        for ec in data.categories:
            result = await session.execute(select(Category).where(Category.name == ec.name))
            obj = result.scalar_one_or_none()
            if obj:
                categories_found += 1
            else:
                obj = Category(name=ec.name, description=ec.description)
                session.add(obj)
            old_category[ec.id] = obj
        await session.flush()

        # 2. Breeds — find-or-create by breed_code
        breeds_found = 0
        for eb in data.breeds:
            result = await session.execute(select(Breed).where(Breed.breed_code == eb.breed_code))
            obj = result.scalar_one_or_none()
            if obj:
                breeds_found += 1
            else:
                cat_id = old_category[eb.category_id].id if eb.category_id and eb.category_id in old_category else None
                obj = Breed(breed_code=eb.breed_code, name=eb.name, category_id=cat_id)
                session.add(obj)
            old_breed[eb.id] = obj
        await session.flush()

        # 3. Judges — always create new
        judges_created = 0
        for ej in data.judges:
            judge = Judge(name=ej.name, flag=ej.flag)
            session.add(judge)
            for cid in ej.category_ids:
                if cid in old_category:
                    judge.categories.append(old_category[cid])
            await session.flush()
            old_judge[ej.id] = judge
            judges_created += 1

        # 4. Show
        show = Show(
            name=data.show.name,
            start_date=data.show.start_date,
            end_date=data.show.end_date,
            status=data.show.status,
        )
        session.add(show)
        await session.flush()

        # 5. Days
        for ed in data.show.days:
            day = ShowDay(show_id=show.id, name=ed.name, sort_order=ed.sort_order)
            session.add(day)
            await session.flush()
            old_day[ed.id] = day

        # 6. Cats — always create new, with CatShowDay entries
        cats_created = 0
        for ec in data.cats:
            owner_id = None
            if ec.owner:
                result = await session.execute(select(Owner).where(Owner.name == ec.owner))
                owner = result.scalar_one_or_none()
                if not owner:
                    owner = Owner(name=ec.owner)
                    session.add(owner)
                    await session.flush()
                owner_id = owner.id
            cat = Cat(
                name=ec.name, breed_ems=ec.breed_ems,
                gender=ec.gender, show_class=ec.show_class,
                birth_date=ec.birth_date, registration_nr=ec.registration_nr,
                owner_id=owner_id, status=ec.status,
            )
            session.add(cat)
            await session.flush()
            for cd_ref in ec.days:
                if cd_ref.show_day_id in old_day:
                    session.add(CatShowDay(
                        cat_id=cat.id,
                        show_day_id=old_day[cd_ref.show_day_id].id,
                        catalog_nr=cd_ref.catalog_nr,
                    ))
            old_cat[ec.id] = cat
            cats_created += 1

        # 7. Rings + RingCategory + RingQueue
        queue_entries = 0
        for ed in data.show.days:
            day = old_day[ed.id]
            for er in ed.rings:
                new_judge_id = old_judge[er.judge_id].id if er.judge_id and er.judge_id in old_judge else None
                ring = Ring(
                    show_day_id=day.id,
                    ring_number=er.ring_number,
                    judge_id=new_judge_id,
                )
                session.add(ring)
                await session.flush()

                for cid in er.category_ids:
                    if cid in old_category:
                        session.add(RingCategory(ring_id=ring.id, category_id=old_category[cid].id))

                for eq in er.queue:
                    if eq.cat_id in old_cat:
                        session.add(RingQueue(
                            ring_id=ring.id,
                            cat_id=old_cat[eq.cat_id].id,
                            sequence_order=eq.sequence_order,
                            status=eq.status,
                        ))
                        queue_entries += 1

        await session.commit()
    except Exception:
        await session.rollback()
        raise

    await manager.broadcast(SHOW_CREATED, {"show_id": show.id})

    return ShowImportResponse(
        show_id=show.id,
        categories_found=categories_found,
        breeds_found=breeds_found,
        judges_created=judges_created,
        cats_created=cats_created,
        queue_entries=queue_entries,
    )


@router.get("/{show_id}/cats", response_model=list[CatWithDaysResponse])
async def list_show_cats(show_id: int, day_id: int | None = None, session: AsyncSession = Depends(get_session)):
    days_query = select(ShowDay).where(ShowDay.show_id == show_id)
    if day_id is not None:
        days_query = days_query.where(ShowDay.id == day_id)
    days_result = await session.execute(days_query)
    day_ids = [d.id for d in days_result.scalars().all()]

    if not day_ids:
        return []

    result = await session.execute(
        select(Cat)
        .join(CatShowDay)
        .where(CatShowDay.show_day_id.in_(day_ids))
        .options(selectinload(Cat.breed_rel), selectinload(Cat.days).selectinload(CatShowDay.day))
        .distinct()
    )
    return [cat_with_days(c) for c in result.scalars().all()]


@router.get("/{show_id}/cat-assignment-progress", response_model=CatAssignmentProgress)
async def get_cat_assignment_progress(show_id: int, session: AsyncSession = Depends(get_session)):
    days_result = await session.execute(
        select(ShowDay.id).where(ShowDay.show_id == show_id)
    )
    day_ids = list(days_result.scalars().all())

    if not day_ids:
        return CatAssignmentProgress(total_cats=0, assigned_cats=0)

    total_result = await session.execute(
        select(func.count(func.distinct(CatShowDay.cat_id)))
        .where(CatShowDay.show_day_id.in_(day_ids))
    )
    total_cats = total_result.scalar() or 0

    assigned_result = await session.execute(
        select(func.count(func.distinct(RingQueue.cat_id)))
        .join(Ring, RingQueue.ring_id == Ring.id)
        .where(Ring.show_day_id.in_(day_ids))
    )
    assigned_cats = assigned_result.scalar() or 0

    return CatAssignmentProgress(total_cats=total_cats, assigned_cats=assigned_cats)
