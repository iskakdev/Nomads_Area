import html
import logging


logger = logging.getLogger(__name__)


def clean(v):
    return html.escape(str(v)) if v is not None else ""

def enqueue_task_safely(task, *args):
    try:
        return task.delay(*args)
    except Exception as exc:
        # Notification delivery must never break a successfully saved lead/booking.
        logger.exception("Failed to enqueue notification task %s: %s", getattr(task, "name", task), exc)
        return None
