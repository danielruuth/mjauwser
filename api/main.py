import asyncio
from contextlib import asynccontextmanager

import jwt

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text as sa_text

from database import engine, Base, async_session_factory
from config import settings
from routers import cats, judges, state, import_csv, breeds as breeds_router
from routers import shows, show_days, connections, display_devices, auth, show_judges, owners
from ws.manager import manager
from dependencies.auth import require_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    for attempt in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Seed categories and breeds if empty
                result = await conn.execute(sa_text("SELECT COUNT(*) FROM categories"))
                count = result.scalar()
                if count == 0:
                    await conn.execute(sa_text("""
                        INSERT INTO categories (id, name, description) VALUES
                        (1, 'Kategori 1', 'Långhår och semilånghår som tävlar strikt efter färg'),
                        (2, 'Kategori 2', 'Semilånghår som tävlar i grupp'),
                        (3, 'Kategori 3', 'Korthår som är lite grövre i typen'),
                        (4, 'Kategori 4', 'Orientaliska raser, mer slanka korthår, rexade korthårsraser samt nakenkatter')
                    """))
                    await conn.execute(sa_text("""
                        INSERT INTO breeds (breed_code, name, category_id) VALUES
                        ('EXO', 'Exotic', 1),
                        ('PER', 'Perser', 1),
                        ('RAG', 'Ragdoll', 1),
                        ('SBI', 'Helig Birma', 1),
                        ('MCO', 'Maine Coon', 2),
                        ('NFO', 'Norsk Skogkatt', 2),
                        ('SIB', 'Sibirisk katt', 2),
                        ('NEM', 'Neva Masquerade', 2),
                        ('TUV', 'Turkisk Van', 2),
                        ('TUA', 'Turkisk Angora', 2),
                        ('BEN', 'Bengal', 3),
                        ('BSH', 'Brittiskt Korthår', 3),
                        ('BLH', 'Brittiskt Långhår', 3),
                        ('BUR', 'Burma', 3),
                        ('OCI', 'Ocicat', 3),
                        ('CRX', 'Cornish Rex', 4),
                        ('DRX', 'Devon Rex', 4),
                        ('OLH', 'Orientaliskt Långhår', 4),
                        ('RUS', 'Russian Blue', 4),
                        ('SIA', 'Siames', 4),
                        ('LYO', 'Lykoi', 4),
                        ('HCS', 'Huskatt', NULL)
                    """))
                    # Sync sequences after explicit ID inserts
                    await conn.execute(sa_text("SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories))"))
                    await conn.execute(sa_text("SELECT setval('breeds_id_seq', (SELECT MAX(id) FROM breeds))"))
                # Migrate existing databases: add status column to cat_show_days if missing
                await conn.execute(sa_text("ALTER TABLE cat_show_days ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'present'"))
            break
        except Exception as e:
            if attempt == 9:
                raise
            print(f"DB not ready (attempt {attempt + 1}/10): {e}")
            await asyncio.sleep(2)
    yield
    await engine.dispose()


app = FastAPI(title="Cat Show Judging System", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cats.router, dependencies=[Depends(require_admin)])
app.include_router(judges.router, dependencies=[Depends(require_admin)])
app.include_router(shows.router, dependencies=[Depends(require_admin)])
app.include_router(show_days.router, dependencies=[Depends(require_admin)])
app.include_router(state.router)
app.include_router(import_csv.router, dependencies=[Depends(require_admin)])
app.include_router(breeds_router.router, dependencies=[Depends(require_admin)])
app.include_router(connections.router, dependencies=[Depends(require_admin)])
app.include_router(display_devices.router, dependencies=[Depends(require_admin)])
app.include_router(show_judges.router, dependencies=[Depends(require_admin)])
app.include_router(owners.router, dependencies=[Depends(require_admin)])
app.include_router(auth.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws-app")
async def websocket_endpoint(
    ws: WebSocket,
    role: str = Query("display"),
    ring_id: int = Query(None),
    device_type: str = Query(None),
    device_id: str = Query(None),
    ring_number: int = Query(None),
    show_id: int = Query(None),
    day_id: int = Query(None),
    token: str = Query(None),
):
    if role == "admin":
        if not token:
            await ws.close(code=4001, reason="Missing token")
            return
        try:
            jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            await ws.close(code=4001, reason="Token expired")
            return
        except jwt.InvalidTokenError:
            await ws.close(code=4001, reason="Invalid token")
            return
        await manager.connect_admin(ws)
    elif role == "display":
        device_name = None
        if device_type == "day_display" and device_id:
            from routers.display_devices import get_or_create_display_device
            async with async_session_factory() as session:
                device = await get_or_create_display_device(session, device_id, show_id, day_id)
                device_name = device.name
        await manager.connect_display(ws, ring_id=ring_id, ring_number=ring_number,
                                      show_id=show_id, day_id=day_id,
                                      device_type=device_type,
                                      device_id=device_id, device_name=device_name)
    elif role == "judge" and ring_id is not None:
        await manager.connect_judge(ws, ring_id, ring_number=ring_number,
                                    show_id=show_id, day_id=day_id)
    else:
        await ws.close(code=4000, reason="Invalid role or missing ring_id")
        return

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception:
        await manager.disconnect(ws)
