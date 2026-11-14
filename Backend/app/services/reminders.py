"""Background job: remind restaurant owners about orders nobody has touched."""
import asyncio
import logging
from datetime import timedelta

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..constants import REMINDER_STATUSES
from ..database import SessionLocal
from ..models import AdminReminderLog, Order, utcnow

logger = logging.getLogger("campusbite.reminders")


def generate_reminders(
    db: Session, restaurant_id: int | None = None, minutes: int | None = None
) -> int:
    """Create a reminder for every PLACED/ACCEPTED order not updated for `minutes`.

    Idempotent: an order gets at most one reminder per stale status
    (also enforced by a unique constraint). Returns how many were created.
    """
    minutes = minutes if minutes is not None else get_settings().reminder_after_minutes
    cutoff = utcnow() - timedelta(minutes=minutes)

    already_reminded = exists().where(
        AdminReminderLog.order_id == Order.id,
        AdminReminderLog.status_at_time == Order.status,
    )
    stmt = select(Order).where(
        Order.status.in_(REMINDER_STATUSES),
        Order.updated_at <= cutoff,
        ~already_reminded,
    )
    if restaurant_id is not None:
        stmt = stmt.where(Order.restaurant_id == restaurant_id)

    created = 0
    for order in db.scalars(stmt).all():
        db.add(
            AdminReminderLog(
                order_id=order.id,
                restaurant_id=order.restaurant_id,
                status_at_time=order.status,
                message=(
                    f"Order #{order.id} has been {order.status} for more than "
                    f"{minutes} minutes without an update"
                ),
            )
        )
        created += 1
    db.commit()
    return created


def run_reminder_job() -> int:
    with SessionLocal() as db:
        created = generate_reminders(db)
    if created:
        logger.info("Created %s order reminder(s)", created)
    return created


async def reminder_loop() -> None:
    """Runs for the lifetime of the app (started from the FastAPI lifespan)."""
    interval = get_settings().reminder_interval_seconds
    logger.info("Reminder job started (every %ss)", interval)
    while True:
        try:
            await asyncio.to_thread(run_reminder_job)
        except Exception:  # keep the loop alive whatever happens
            logger.exception("Reminder job failed")
        await asyncio.sleep(interval)
