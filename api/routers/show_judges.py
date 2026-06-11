from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, delete as sa_delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Judge, Show, judge_categories, judge_shows
from schemas import JudgeCreate, JudgeResponse, ShowJudgeAdd
from ws.events import JUDGE_CREATED, SHOW_JUDGE_ASSIGNED, SHOW_JUDGE_UNASSIGNED
from ws.manager import manager

router = APIRouter(prefix="/api/shows", tags=["show_judges"])


@router.get("/{show_id}/judges", response_model=list[JudgeResponse])
async def list_show_judges(show_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Show).where(Show.id == show_id).options(
            selectinload(Show.judges).selectinload(Judge.categories),
        )
    )
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(404, "Show not found")
    return show.judges


@router.post("/{show_id}/judges", response_model=None, status_code=201)
async def add_show_judge(show_id: int, body: ShowJudgeAdd, session: AsyncSession = Depends(get_session)):
    show_result = await session.execute(select(Show).where(Show.id == show_id))
    show = show_result.scalar_one_or_none()
    if not show:
        raise HTTPException(404, "Show not found")

    if body.judge_ids:
        # Assign multiple existing judges
        assigned: list[Judge] = []
        for jid in body.judge_ids:
            judge_result = await session.execute(
                select(Judge).where(Judge.id == jid).options(selectinload(Judge.categories))
            )
            judge = judge_result.scalar_one_or_none()
            if not judge:
                continue
            existing = await session.execute(
                select(judge_shows).where(
                    judge_shows.c.judge_id == jid,
                    judge_shows.c.show_id == show_id,
                )
            )
            if existing.first():
                continue
            await session.execute(
                insert(judge_shows).values(judge_id=jid, show_id=show_id)
            )
            assigned.append(judge)
        await session.commit()
        for judge in assigned:
            await session.refresh(judge, ["categories"])
        if assigned:
            await manager.broadcast(SHOW_JUDGE_ASSIGNED, {
                "show_id": show_id,
                "judge_ids": [j.id for j in assigned],
            })
        return assigned[0] if assigned else None

    if body.judge_id is not None:
        # Assign single existing judge to show
        judge_result = await session.execute(
            select(Judge).where(Judge.id == body.judge_id).options(selectinload(Judge.categories))
        )
        judge = judge_result.scalar_one_or_none()
        if not judge:
            raise HTTPException(404, "Judge not found")
        existing = await session.execute(
            select(judge_shows).where(
                judge_shows.c.judge_id == body.judge_id,
                judge_shows.c.show_id == show_id,
            )
        )
        if existing.first():
            raise HTTPException(409, "Judge already assigned to this show")
        await session.execute(
            insert(judge_shows).values(judge_id=body.judge_id, show_id=show_id)
        )
        await session.commit()
        await session.refresh(judge, ["categories"])
        await manager.broadcast(SHOW_JUDGE_ASSIGNED, {
            "show_id": show_id,
            "judge_ids": [body.judge_id],
        })
        return judge

    # Create new judge and assign to show
    if not body.name:
        raise HTTPException(422, "Name is required when creating a new judge")
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
    await session.execute(
        insert(judge_shows).values(judge_id=judge.id, show_id=show_id)
    )
    await session.commit()
    await session.refresh(judge, ["categories"])
    await manager.broadcast(JUDGE_CREATED, {"judge": JudgeResponse.model_validate(judge).model_dump()})
    return judge


@router.delete("/{show_id}/judges/{judge_id}", status_code=204)
async def remove_show_judge(show_id: int, judge_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(judge_shows).where(
            judge_shows.c.judge_id == judge_id,
            judge_shows.c.show_id == show_id,
        )
    )
    if not result.first():
        raise HTTPException(404, "Judge not assigned to this show")
    await session.execute(
        sa_delete(judge_shows).where(
            judge_shows.c.judge_id == judge_id,
            judge_shows.c.show_id == show_id,
        )
    )
    await session.commit()
    await manager.broadcast(SHOW_JUDGE_UNASSIGNED, {
        "show_id": show_id,
        "judge_id": judge_id,
    })
