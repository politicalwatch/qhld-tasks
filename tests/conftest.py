"""Shared, repo-wide test configuration.

``tipi_tasks`` imports ``tipi_data`` (transitively, via its repositories), and
``tipi_data`` builds its ``MongoClient`` at import time from the ``MONGO_*`` vars — so
they must be in place before anything under ``tipi_tasks`` is imported, including the
DB-free unit tests. The values point at a throwaway test database on a **fixed** host
port; the integration tier (``tests/integration/conftest.py``) starts the matching
container. ``MONGO_SKIP_INDEX_INIT`` keeps the import-time index creation from
connecting, so unit tests import offline with no MongoDB.

The fixed port (47018) is deliberately distinct from qhld-data's (47017) so both test
suites can run on the same host without their throwaway containers colliding.

Tiers:
- ``tests/unit`` — no infrastructure; runs anywhere (``-m unit``).
- ``tests/integration`` — needs the throwaway Mongo; auto-skips without Docker
  (``-m integration``).
"""

import os

os.environ.setdefault("MONGO_SKIP_INDEX_INIT", "1")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("MONGO_PORT", "47018")
os.environ.setdefault("MONGO_USER", "qhld")
os.environ.setdefault("MONGO_PASSWORD", "qhld")
os.environ.setdefault("MONGO_DB_NAME", "qhlddb_test")
