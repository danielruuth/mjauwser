from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, delete as sa_delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Judge, Ring, judge_categories
from schemas import JudgeCreate, JudgeUpdate, JudgeResponse
from ws.events import JUDGE_CREATED, JUDGE_UPDATED, JUDGE_DELETED
from ws.manager import manager

router = APIRouter(prefix="/api/judges", tags=["judges"])


@router.get("", response_model=list[JudgeResponse])
async def list_judges(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Judge).order_by(Judge.name).options(selectinload(Judge.categories))
    )
    return result.scalars().all()


@router.get("/{judge_id}", response_model=JudgeResponse)
async def get_judge(judge_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Judge).where(Judge.id == judge_id).options(selectinload(Judge.categories))
    )
    judge = result.scalar_one_or_none()
    if not judge:
        raise HTTPException(404, "Judge not found")
    return judge


@router.post("", response_model=JudgeResponse, status_code=201)
async def create_judge(body: JudgeCreate, session: AsyncSession = Depends(get_session)):
    judge = Judge(
        name=body.name,
        photo=body.photo,
        bio=body.bio,
        flag=body.flag,
    )
    session.add(judge)
    await session.flush()
    if body.category_ids:
        for cat_id in body.category_ids:
            await session.execute(
                insert(judge_categories).values(judge_id=judge.id, category_id=cat_id)
            )
    await session.commit()
    await session.refresh(judge, ["categories"])
    await manager.broadcast(JUDGE_CREATED, {"judge": JudgeResponse.model_validate(judge).model_dump()})
    return judge


@router.put("/{judge_id}", response_model=JudgeResponse)
async def update_judge(judge_id: int, body: JudgeUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Judge).where(Judge.id == judge_id).options(selectinload(Judge.categories))
    )
    judge = result.scalar_one_or_none()
    if not judge:
        raise HTTPException(404, "Judge not found")
    update_data = body.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)
    for key, value in update_data.items():
        setattr(judge, key, value)
    if category_ids is not None:
        await session.execute(sa_delete(judge_categories).where(judge_categories.c.judge_id == judge_id))
        for cat_id in category_ids:
            await session.execute(
                insert(judge_categories).values(judge_id=judge_id, category_id=cat_id)
            )
    await session.commit()
    await session.refresh(judge, ["categories"])
    await manager.broadcast(JUDGE_UPDATED, {"judge": JudgeResponse.model_validate(judge).model_dump()})
    return judge


@router.delete("/{judge_id}", status_code=204)
async def delete_judge(judge_id: int, session: AsyncSession = Depends(get_session)):
    judge = await session.get(Judge, judge_id)
    if not judge:
        raise HTTPException(404, "Judge not found")
    await session.delete(judge)
    await session.commit()
    await manager.broadcast(JUDGE_DELETED, {"judge_id": judge_id})


@router.get("/{judge_id}/rings")
async def get_judge_rings(judge_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Judge).where(Judge.id == judge_id))
    judge = result.scalar_one_or_none()
    if not judge:
        raise HTTPException(404, "Judge not found")

    rings_result = await session.execute(
        select(Ring).where(Ring.judge_id == judge_id).options(
            selectinload(Ring.categories),
            selectinload(Ring.day),
        )
    )
    rings = rings_result.scalars().all()
    return [
        {
            "id": r.id,
            "ring_number": r.ring_number,
            "day_id": r.show_day_id,
            "day_name": r.day.name if r.day else "",
            "show_id": r.day.show_id if r.day else None,
            "status": r.status,
            "current_catalog_nr": r.current_catalog_nr,
        }
        for r in rings
    ]
