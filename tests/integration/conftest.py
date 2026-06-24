"""Integration-tier fixtures.

These tests need a reachable MongoDB; a throwaway ``mongo`` container is started
automatically for the session via ``testcontainers`` and torn down at the end — no
manual setup and no risk of touching real data. When Docker is unavailable the tests
**skip** rather than fail, so a plain ``uv run pytest`` stays green anywhere.

The container is published on the **fixed** host port the ``tipi_data`` client was
built against in the root ``conftest.py`` (the client is built at import time, so the
port must be known up front; it is lazy, so the container can start later).
"""

import os
from unittest.mock import MagicMock

import pytest
from pymongo.errors import PyMongoError

from tipi_data import client, db, ensure_indexes

_HOST_PORT = int(os.environ["MONGO_PORT"])


@pytest.fixture(scope="session")
def _mongo_container():
    """A throwaway MongoDB for the test session, published on the fixed host port.
    Skips all dependent tests when Docker is unavailable. Torn down at session end."""
    from testcontainers.mongodb import MongoDbContainer

    container = (
        MongoDbContainer("mongo:7.0", username="qhld", password="qhld")
        .with_bind_ports(27017, _HOST_PORT)
    )
    try:
        container.start()
    except Exception as exc:  # docker missing / daemon down / port in use
        pytest.skip(f"No Docker available for MongoDB integration tests: {exc}")
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def mongo_db(_mongo_container):
    """The test database, reset before and after each test. Drops all collections so
    each test starts clean, then creates the declared indexes."""
    # Guard: the drop loop below is destructive, so refuse to run against anything that
    # is not an explicit test database — never the prod-data ``qhlddb``.
    assert db.name.endswith("_test"), (
        f"refusing to run destructive tests against database {db.name!r}; "
        "the test database name must end in '_test'"
    )
    try:
        client.admin.command("ping")
    except PyMongoError:
        pytest.skip("No MongoDB reachable for task integration tests")

    for name in db.list_collection_names():
        db.drop_collection(name)
    ensure_indexes()
    yield db
    for name in db.list_collection_names():
        db.drop_collection(name)


@pytest.fixture
def seed_alert_dumps(mongo_db):
    """Load the real demo ``alerts`` + ``initiatives_alerts`` dumps into the throwaway
    DB, so ``send_alerts`` runs against realistic data. Returns the inserted docs."""
    from tests.fixtures_loader import load_json_dump

    return {
        "alerts": load_json_dump(mongo_db, "alerts", "alerts.json"),
        "initiatives_alerts": load_json_dump(
            mongo_db, "initiatives_alerts", "initiatives_alerts.json"
        ),
    }


@pytest.fixture
def no_email(monkeypatch):
    """Replace the module-bound ``send_email`` in every task module with a single
    recording mock — no SparkPost, no network. The tasks do
    ``from .mail import send_email``, so each module holds its own reference that must
    be patched individually. Returns the shared mock so tests can assert call args."""
    import tipi_tasks.alerts
    import tipi_tasks.scanned
    import tipi_tasks.validate

    mock = MagicMock(name="send_email")
    for module in (tipi_tasks.alerts, tipi_tasks.scanned, tipi_tasks.validate):
        monkeypatch.setattr(module, "send_email", mock)
    return mock
