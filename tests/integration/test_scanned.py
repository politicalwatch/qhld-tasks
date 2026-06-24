"""Integration tests for the ``scanned`` document-maintenance tasks, against a
throwaway MongoDB. ``send_email`` is replaced by the ``no_email`` recording mock.
"""

from datetime import datetime, timedelta

import pytest

from tipi_tasks.scanned import clean_documents, notify_new_documents

pytestmark = pytest.mark.integration


def test_clean_documents_deletes_only_expired(mongo_db):
    now = datetime.now()
    mongo_db.scanned.insert_many([
        {"_id": "expired", "expiration": now - timedelta(days=10)},
        {"_id": "live", "expiration": now + timedelta(days=10)},
    ])

    clean_documents()

    remaining = {d["_id"] for d in mongo_db.scanned.find()}
    assert remaining == {"live"}


def test_notify_new_documents_noop_when_none(mongo_db, no_email):
    # Only a verified doc exists, so there is nothing to notify about.
    mongo_db.scanned.insert_one({
        "_id": "verified",
        "created": datetime.now() - timedelta(hours=1),
        "verified": True,
    })

    notify_new_documents()

    no_email.assert_not_called()


@pytest.mark.xfail(
    strict=True,
    reason="BUG 1b6b061 (2024): notify_new_documents is broken end-to-end and cannot "
    "send. It first crashes on a dead reference to config.TIPI_FRONTEND (never defined "
    "in config.py), and even past that calls send_email with 4 args, omitting "
    "mail_config (so the documents context lands in the mail_config slot). Both defects "
    "predate the migrations. Fix later via TDD.",
)
def test_notify_new_documents_sends_with_documents_in_context(mongo_db, no_email):
    mongo_db.scanned.insert_one({
        "_id": "fresh",
        "title": "Documento nuevo",
        "created": datetime.now() - timedelta(hours=1),
        "verified": False,
    })

    notify_new_documents()

    no_email.assert_called_once()
    args, _ = no_email.call_args
    # Correct signature mirrors the other callers:
    # (recipients, subject, template, mail_config, context).
    assert args[0] == ["info@politicalwatch.es"]
    context = args[4]
    assert len(context["documents"]) == 1
