"""Celery tasks for the colorization pipeline.

Exposes ``analyze_page`` (CPU) and ``colorize_page`` (GPU) so they can be
discovered by ``app.workers.celery_app`` via its ``include`` setting.
"""

from app.workers.tasks.colorization_tasks import analyze_page, colorize_page

__all__ = ["analyze_page", "colorize_page"]
