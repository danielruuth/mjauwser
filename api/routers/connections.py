from fastapi import APIRouter

from ws.manager import manager
from schemas import ConnectionResponse

router = APIRouter(prefix="/api", tags=["connections"])


@router.get("/connections", response_model=list[ConnectionResponse])
async def get_connections():
    return manager.get_connections()
