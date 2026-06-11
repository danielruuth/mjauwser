import csv
import io
import json
import re
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Cat, Owner, Breed, Show, ShowDay, CatShowDay
from schemas import CatResponse, OwnerResponse
from ws.events import CAT_CREATED
from ws.manager import manager

router = APIRouter(prefix="/api/cats/import", tags=["import"])

DB_FIELDS = [
    "catalog_nr", "name", "breed_ems", "gender", "show_class",
    "birth_date", "registration_nr", "status",
]

FIELD_KEYWORDS = {
    "catalog_nr": ["catalog", "catalognr", "catalog_nr", "catalog#", "nr", "number", "id", "cat#", "entry"],
    "name": ["name", "cat name", "catname", "kitten name"],
    "breed_ems": ["breed", "breed_ems", "breedcode", "ems", "ras", "race", "kod", "code"],
    "gender": ["gender", "sex", "kön"],
    "show_class": ["class", "klass", "show_class", "category", "kategori", "division"],
    "birth_date": ["birth", "birth_date", "birthdate", "born", "dob", "födelsedatum", "född"],
    "registration_nr": ["registration", "registration_nr", "reg_nr", "regnr", "reg#", "register", "registreringsnummer"],
    "owner": ["owner", "ägare", "uppfödare", "breeder"],
    "status": ["status", "present", "absent"],
}


def _auto_detect_mapping(headers: list[str]) -> dict[str, str]:
    mapping = {}
    used = set()
    for header in headers:
        normalized = re.sub(r"[^a-z0-9]", "", header.lower())
        best_match: Optional[str] = None
        for field, keywords in FIELD_KEYWORDS.items():
            if field in used:
                continue
            for kw in keywords:
                kw_norm = re.sub(r"[^a-z0-9]", "", kw.lower())
                if normalized == kw_norm or normalized.endswith(kw_norm) or kw_norm.endswith(normalized):
                    best_match = field
                    break
            if best_match:
                break
        if best_match:
            used.add(best_match)
            mapping[header] = best_match
        else:
            mapping[header] = ""
    return mapping


def _parse_file(filename: str, content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if filename.lower().endswith(".json"):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        data = json.loads(text)
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    data = v
                    break
            else:
                raise HTTPException(400, "JSON object must contain an array of entries")
        if not isinstance(data, list):
            raise HTTPException(400, "JSON must be an array or an object containing an array")
        if not data:
            raise HTTPException(400, "JSON array is empty")
        headers = list(data[0].keys()) if data else []
        rows = [{k: str(v) if v is not None else "" for k, v in item.items()} for item in data]
        return headers, rows
    elif filename.lower().endswith(".csv"):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except UnicodeDecodeError:
                raise HTTPException(400, "Could not decode CSV. Use UTF-8 or Latin-1.")
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        if not headers:
            raise HTTPException(400, "CSV file has no headers")
        rows = [row for row in reader]
        return headers, rows
    else:
        raise HTTPException(400, "File must be .csv or .json")


def _parse_catalog_nr(val: str, num_days: int) -> list[int | None]:
    """Parse catalog_nr field. Supports JSON array or plain int."""
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            normalized = val.replace("False", "false").replace("True", "true").replace("None", "null")
            parsed = json.loads(normalized)
            if not isinstance(parsed, list):
                return [int(parsed)] if parsed else []
            result = []
            for item in parsed:
                if item is False or item is None or item == "":
                    result.append(None)
                else:
                    result.append(int(item))
            # Pad or truncate to match number of days
            while len(result) < num_days:
                result.append(None)
            return result[:num_days]
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid catalog_nr array: {val}")
    else:
        # Single value — assign to first day only
        try:
            first = [int(val)] if val else [None]
            while len(first) < num_days:
                first.append(None)
            return first[:num_days]
        except ValueError:
            raise HTTPException(400, f"Invalid catalog_nr: {val}")


async def _process_rows(
    rows: list[dict[str, str]],
    column_mapping: dict[str, str],
    session: AsyncSession,
    show_id: int | None = None,
) -> tuple[int, list[dict]]:
    breeds_result = await session.execute(select(Breed))
    valid_breed_codes = {b.breed_code for b in breeds_result.scalars().all()}

    # Load days for this show
    days: list[ShowDay] = []
    if show_id:
        days_result = await session.execute(
            select(ShowDay).where(ShowDay.show_id == show_id).order_by(ShowDay.sort_order)
        )
        days = list(days_result.scalars().all())

    imported = 0
    errors: list[dict] = []

    for row_number, row in enumerate(rows, start=1):
        try:
            cat_data: dict[str, str] = {}
            for src_col, db_field in column_mapping.items():
                if not db_field:
                    continue
                val = row.get(src_col, "").strip()
                if val:
                    cat_data[db_field] = val

            catalog_raw = cat_data.get("catalog_nr", "")
            if not catalog_raw:
                errors.append({"row": row_number, "error": "Missing catalog_nr"})
                continue
            if "name" not in cat_data:
                errors.append({"row": row_number, "error": "Missing name"})
                continue
            if "breed_ems" not in cat_data:
                errors.append({"row": row_number, "error": "Missing breed_ems"})
                continue

            gender_raw = cat_data.get("gender", "").strip().lower()
            gender_map = {"hona": "F", "hane": "M", "female": "F", "male": "M", "f": "F", "m": "M", "hon hona": "F", "han hane": "M"}
            gender_norm = gender_map.get(gender_raw, gender_raw[:1].upper() if gender_raw else "")
            if gender_norm not in ("M", "F"):
                errors.append({"row": row_number, "error": f"Missing or invalid gender (must be M or F), got '{cat_data.get('gender', '')}'"})
                continue
            if "show_class" not in cat_data:
                errors.append({"row": row_number, "error": "Missing show_class"})
                continue

            breed_ems = cat_data["breed_ems"].strip().upper().split()[0]
            if breed_ems not in valid_breed_codes:
                errors.append({"row": row_number, "error": f"Unknown breed_ems '{breed_ems}'"})
                continue

            catalog_values = _parse_catalog_nr(catalog_raw, len(days))

            owner_id = None
            owner_name = cat_data.get("owner")
            if owner_name:
                result = await session.execute(select(Owner).where(Owner.name == owner_name))
                owner = result.scalar_one_or_none()
                if not owner:
                    owner = Owner(name=owner_name)
                    session.add(owner)
                    await session.flush()
                owner_id = owner.id

            cat = Cat(
                name=cat_data["name"],
                breed_ems=breed_ems,
                gender=gender_norm,
                show_class=cat_data["show_class"],
                birth_date=cat_data.get("birth_date"),
                registration_nr=cat_data.get("registration_nr"),
                owner_id=owner_id,
                status=cat_data.get("status", "present"),
            )
            session.add(cat)
            await session.flush()

            # Create CatShowDay entries
            for i, day in enumerate(days):
                cnr = catalog_values[i] if i < len(catalog_values) else None
                if cnr is not None:
                    # Check uniqueness
                    existing_csd = await session.execute(
                        select(CatShowDay).where(
                            CatShowDay.show_day_id == day.id,
                            CatShowDay.catalog_nr == cnr,
                        )
                    )
                    if existing_csd.scalar_one_or_none():
                        errors.append({"row": row_number, "error": f"Catalog nr {cnr} already exists on day '{day.name}'"})
                        continue
                    session.add(CatShowDay(cat_id=cat.id, show_day_id=day.id, catalog_nr=cnr))

            await session.flush()
            await session.refresh(cat, ["breed_rel", "owner_rel"])
            resp = CatResponse(
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
            await manager.broadcast(CAT_CREATED, {"cat": resp.model_dump()})
            imported += 1
        except Exception as e:
            errors.append({"row": row_number, "error": str(e)})

    return imported, errors


@router.post("/preview")
async def preview_import(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    content = await file.read()
    headers, all_rows = _parse_file(file.filename, content)

    rows_preview = all_rows[:10]
    auto_mapping = _auto_detect_mapping(headers)

    return {
        "headers": headers,
        "total_estimated": len(all_rows),
        "rows": rows_preview,
        "auto_mapping": auto_mapping,
        "db_fields": DB_FIELDS,
    }


@router.post("")
async def import_file(
    file: UploadFile = File(...),
    mapping: str = Form(...),
    show_id: int = Query(None),
    session: AsyncSession = Depends(get_session),
):
    try:
        column_mapping: dict[str, str] = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid mapping JSON")

    if show_id:
        show = await session.get(Show, show_id)
        if not show:
            raise HTTPException(400, "Show not found")

    content = await file.read()
    _, rows = _parse_file(file.filename, content)

    imported, errors = await _process_rows(rows, column_mapping, session, show_id=show_id)
    await session.commit()

    return {"imported": imported, "errors": errors, "total": imported + len(errors)}
