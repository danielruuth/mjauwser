from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload, defaultload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Judge, Cat, Owner, Show, ShowDay, Breed, Category, Ring
from schemas import JudgeResponse, CatResponse, OwnerResponse, StateResponse, BreedResponse, CategoryResponse
from response_helpers import show_detail_response

router = APIRouter(prefix="/api", tags=["state"])


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


@router.get("/state", response_model=StateResponse)
async def get_full_state(session: AsyncSession = Depends(get_session)):
    judges_result = await session.execute(
        select(Judge).order_by(Judge.name).options(selectinload(Judge.categories))
    )
    cats_result = await session.execute(
        select(Cat).order_by(Cat.id).options(selectinload(Cat.breed_rel), selectinload(Cat.owner_rel))
    )
    shows_result = await session.execute(
        select(Show).order_by(Show.id).options(
            selectinload(Show.days)
                .selectinload(ShowDay.rings)
                    .selectinload(Ring.judge_rel)
                        .selectinload(Judge.categories),
            defaultload(Show.days)
                .defaultload(ShowDay.rings)
                    .selectinload(Ring.categories),
        )
    )
    breeds_result = await session.execute(
        select(Breed).order_by(Breed.name).options(selectinload(Breed.category))
    )
    categories_result = await session.execute(select(Category).order_by(Category.id))

    shows = [show_detail_response(s) for s in shows_result.scalars().all()]

    return StateResponse(
        judges=[JudgeResponse.model_validate(j) for j in judges_result.scalars().all()],
        cats=[_cat_to_response(c) for c in cats_result.scalars().all()],
        shows=shows,
        breeds=[BreedResponse.model_validate(b) for b in breeds_result.scalars().all()],
        categories=[CategoryResponse.model_validate(c) for c in categories_result.scalars().all()],
    )
