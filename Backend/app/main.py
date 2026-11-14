import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, SessionLocal, engine
from .middleware import register_middleware
from .routers import ai, auth, delivery, orders, owner, restaurants
from .services.reminders import reminder_loop
from .services.seed import seed_demo_data

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
)
logger = logging.getLogger("campusbite")
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)  # create tables on first start

    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_demo_data(db)

    task = None
    if settings.enable_background_tasks:
        task = asyncio.create_task(reminder_loop())
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="CampusBite API",
    description="Restaurant ordering and delivery backend (FastAPI + SQLAlchemy).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"],
)
register_middleware(app)

app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(orders.router)
app.include_router(owner.router)
app.include_router(delivery.router)
app.include_router(ai.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
