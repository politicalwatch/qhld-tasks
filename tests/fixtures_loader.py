"""Load real demo-data dumps into a (throwaway) MongoDB for tests.

The dumps under ``tests/fixtures/`` are mongoexport-style **extended JSON** arrays
(``{"$date": ...}`` / ``{"$oid": ...}``), parsed with ``bson.json_util`` so dates and
ObjectIds round-trip to native types. They are copies of the user's demo ``alerts`` /
``initiatives_alerts`` collections, used to exercise ``send_alerts`` against realistic
data in the integration test (``tests/integration/test_alerts.py``).
"""

from pathlib import Path

from bson import json_util

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_json_dump(db, collection, filename):
    """Insert an extended-JSON array dump into ``db[collection]``; return the docs."""
    docs = json_util.loads((FIXTURES_DIR / filename).read_text())
    if docs:
        db[collection].insert_many(docs)
    return docs
