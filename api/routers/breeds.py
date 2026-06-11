from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Breed, Category
from schemas import (
    BreedResponse, BreedCreate, BreedUpdate,
    CategoryResponse, CategoryCreate, CategoryUpdate,
)

router = APIRouter(prefix="/api", tags=["breeds"])


# ── Breeds ──

@router.get("/breeds", response_model=list[BreedResponse])
async def list_breeds(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Breed).order_by(Breed.name).options(selectinload(Breed.category))
    )
    return result.scalars().all()


@router.post("/breeds", response_model=BreedResponse, status_code=201)
async def create_breed(body: BreedCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(Breed).where(Breed.breed_code == body.breed_code.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Breed code '{body.breed_code.upper()}' already exists")
    breed = Breed(breed_code=body.breed_code.upper(), name=body.name, category_id=body.category_id)
    session.add(breed)
    await session.commit()
    await session.refresh(breed, ["category"])
    return breed


@router.put("/breeds/{breed_id}", response_model=BreedResponse)
async def update_breed(breed_id: int, body: BreedUpdate, session: AsyncSession = Depends(get_session)):
    breed = await session.get(Breed, breed_id, options=[selectinload(Breed.category)])
    if not breed:
        raise HTTPException(404, "Breed not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(breed, key, value)
    await session.commit()
    await session.refresh(breed, ["category"])
    return breed


@router.delete("/breeds/{breed_id}", status_code=204)
async def delete_breed(breed_id: int, session: AsyncSession = Depends(get_session)):
    breed = await session.get(Breed, breed_id)
    if not breed:
        raise HTTPException(404, "Breed not found")
    await session.delete(breed)
    await session.commit()


# ── Categories ──

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category).order_by(Category.id))
    return result.scalars().all()


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(body: CategoryCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(Category).where(Category.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Category '{body.name}' already exists")
    cat = Category(name=body.name, description=body.description)
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, body: CategoryUpdate, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cat, key, value)
    await session.commit()
    await session.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session)):
    cat = await session.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    await session.delete(cat)
    await session.commit()
