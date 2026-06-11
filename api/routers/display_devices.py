from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_session
from models import DisplayDevice
from schemas import DisplayDeviceResponse, DisplayDeviceUpdate
from ws.events import DEVICE_RENAMED
from ws.manager import manager

router = APIRouter(prefix="/api", tags=["display_devices"])


@router.get("/shows/{show_id}/display-devices", response_model=list[DisplayDeviceResponse])
async def list_display_devices(show_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(DisplayDevice).where(DisplayDevice.show_id == show_id)
    )
    return result.scalars().all()


@router.put("/display-devices/{device_id}", response_model=DisplayDeviceResponse)
async def rename_display_device(device_id: str, body: DisplayDeviceUpdate,
                                 session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(DisplayDevice).where(DisplayDevice.device_id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    device.name = body.name
    await session.commit()
    await session.refresh(device)

    await manager.broadcast(DEVICE_RENAMED, {
        "device_id": device.device_id,
        "name": device.name,
        "show_id": device.show_id,
        "day_id": device.day_id,
    })

    return device


async def get_or_create_display_device(session: AsyncSession, device_id: str,
                                       show_id: int | None, day_id: int | None) -> DisplayDevice:
    result = await session.execute(
        select(DisplayDevice).where(DisplayDevice.device_id == device_id)
    )
    device = result.scalar_one_or_none()
    if device:
        device.last_connected_at = datetime.utcnow()
        if show_id is not None:
            device.show_id = show_id
        if day_id is not None:
            device.day_id = day_id
    else:
        device = DisplayDevice(
            device_id=device_id,
            name="Unnamed Display",
            device_type="day_display",
            show_id=show_id,
            day_id=day_id,
            last_connected_at=datetime.utcnow(),
        )
        session.add(device)
    await session.commit()
    await session.refresh(device)
    return device
