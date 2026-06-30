"""Integration test for ``send_alerts`` against a throwaway MongoDB, seeded with the
**real demo dumps** (``tests/fixtures/``). ``send_email`` is replaced by the
``no_email`` recording mock — no SparkPost, no network — so this asserts the alert is
assembled and dispatched correctly without sending anything.

The demo data: one validated alert (subscribed to topic "España vaciada", kb
``politicas``) and three ``initiatives_alerts`` all tagged ``politicas`` /
"España vaciada", so the alert's ``dbsearch`` matches all three.
"""

import pytest

from tests.fixtures_loader import load_json_dump
from tipi_tasks.alerts import send_alerts

pytestmark = pytest.mark.integration

ALERT_EMAIL = "alex.ahumada@politicalwatch.es"
EXPECTED_INITIATIVE_IDS = {"162-000001", "120-000001", "184-000001"}


def test_send_alerts_dispatches_one_email_with_matching_initiatives(
    mongo_db, seed_alert_dumps, no_email
):
    send_alerts()

    # One validated alert, one kb (politicas) with matches -> exactly one email.
    no_email.assert_called_once()
    args, _ = no_email.call_args
    # send_email([alert.email], subject, template, mail_config, context)
    assert args[0] == [ALERT_EMAIL]

    context = args[4]
    initiatives = context["alert"]["searches"][0]["initiatives"]
    assert {i["id"] for i in initiatives} == EXPECTED_INITIATIVE_IDS

    # The working collection is dropped at the end of the run.
    assert mongo_db.initiatives_alerts.count_documents({}) == 0


def test_send_alerts_drops_response_when_title_is_duplicated(mongo_db, no_email):
    """A "Respuesta" sharing its ``title`` with another initiative in the same group
    is dropped before the email is built; a "Respuesta" with a unique title is kept.

    Seeded from ``initiatives_alerts_respuesta.json`` (three initiatives, all tagged
    ``politicas`` / "España vaciada" so the demo alert's ``dbsearch`` matches them):
    - ``184-000010`` — the question, kept.
    - ``184-000010-respuesta`` — same title as ``184-000010``, ``Respuesta``: dropped.
    - ``184-000012`` — ``Respuesta`` with a unique title: kept.
    """
    load_json_dump(mongo_db, "alerts", "alerts.json")
    load_json_dump(
        mongo_db, "initiatives_alerts", "initiatives_alerts_deduplication.json"
    )

    send_alerts()

    no_email.assert_called_once()
    context = no_email.call_args[0][4]
    initiatives = context["alert"]["searches"][0]["initiatives"]
    assert {i["id"] for i in initiatives} == {"184-000010", "184-000012"}
