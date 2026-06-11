from models import Show, ShowDay, Ring, Judge, RingCategory, Category
from schemas import (
    ShowDetailResponse, ShowDayFullResponse, RingResponse,
    JudgeResponse, CategoryResponse,
)


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


def show_detail_response(show: Show) -> ShowDetailResponse:
    days = []
    for d in (show.days or []):
        rings = [_ring_to_response(r) for r in (d.rings or [])]
        days.append(ShowDayFullResponse(
            id=d.id,
            show_id=d.show_id,
            name=d.name,
            sort_order=d.sort_order,
            rings=rings,
        ))
    return ShowDetailResponse(
        id=show.id,
        name=show.name,
        start_date=show.start_date,
        end_date=show.end_date,
        status=show.status,
        days=days,
    )
