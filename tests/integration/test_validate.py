"""Integration tests for the alert-cleanup tasks (``validate``), against a throwaway
MongoDB. These mutate the ``alerts`` collection via the qhld-data ``Alerts`` repo.
"""

import json
from datetime import date, datetime, timedelta

import pytest

from tipi_tasks import config
from tipi_tasks.validate import clean_alerts_with_past_dates, clean_emails

pytestmark = pytest.mark.integration


def test_clean_emails_removes_timed_out_searches_and_empty_alerts(mongo_db):
    now = datetime.now()
    stale = now - timedelta(days=config.VALIDATION_TIMEOUT + 10)
    recent = now - timedelta(days=1)
    mongo_db.alerts.insert_many([
        # Only search is unvalidated + past the timeout -> removed -> alert emptied -> deleted.
        {"_id": "stale", "email": "stale@x.es",
         "searches": [{"hash": "h-stale", "validated": False, "created": stale}]},
        # Unvalidated but recent -> kept.
        {"_id": "fresh", "email": "fresh@x.es",
         "searches": [{"hash": "h-fresh", "validated": False, "created": recent}]},
    ])

    clean_emails()

    remaining = {d["_id"]: d for d in mongo_db.alerts.find()}
    assert set(remaining) == {"fresh"}
    assert [s["hash"] for s in remaining["fresh"]["searches"]] == ["h-fresh"]


def test_clean_alerts_with_past_dates_removes_only_past_enddates(mongo_db):
    assert str(date.today()) >= "2000-01-01"  # sanity: "past" really is in the past
    mongo_db.alerts.insert_one({
        "_id": "a1", "email": "a@x.es",
        "searches": [
            {"hash": "past", "validated": True,
             "search": json.dumps({"enddate": "2000-01-01"})},
            {"hash": "future", "validated": True,
             "search": json.dumps({"enddate": "2999-12-31"})},
        ],
    })

    clean_alerts_with_past_dates()

    stored = mongo_db.alerts.find_one({"_id": "a1"})
    assert stored is not None
    assert [s["hash"] for s in stored["searches"]] == ["future"]
