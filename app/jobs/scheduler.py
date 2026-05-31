import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.jobs.daily_overdue import detect_overdue_invoices
from app.jobs.monthly_invoicing import generate_monthly_invoices

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        generate_monthly_invoices,
        trigger="cron",
        day=1,
        hour=6,
        minute=0,
        id="monthly_invoicing",
        name="Generate monthly invoices",
        replace_existing=True,
    )

    scheduler.add_job(
        detect_overdue_invoices,
        trigger="cron",
        hour=7,
        minute=0,
        id="daily_overdue",
        name="Detect overdue invoices",
        replace_existing=True,
    )

    logger.info("APScheduler jobs registered")
    scheduler.start()
    logger.info("APScheduler started")
