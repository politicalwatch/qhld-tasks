"""Unit tests for the Celery beat schedule. A scheduled entry naming a task the worker
has not registered is accepted by beat and then discarded on receipt, so a typo here
costs nothing at import time and silently stops the periodic tasks.
"""

import pytest

import tipi_tasks

pytestmark = pytest.mark.unit


def test_every_scheduled_task_is_registered():
    registered = set(tipi_tasks.app.tasks)
    scheduled = {entry["task"] for entry in tipi_tasks.beat_schedule.values()}

    assert scheduled <= registered


def test_init_keeps_the_schedule_resolvable():
    """``init()`` rebuilds the app (business.py calls it before dispatching); the
    rebuilt app must still resolve every scheduled name."""
    tipi_tasks.init()

    registered = set(tipi_tasks.app.tasks)
    scheduled = {entry["task"] for entry in tipi_tasks.app.conf.beat_schedule.values()}

    assert scheduled <= registered
