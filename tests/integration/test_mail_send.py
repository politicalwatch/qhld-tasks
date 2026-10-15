"""Live check that an email really goes out through Mailtrap: sends one message with
the real API and asserts Mailtrap accepted it. Skipped unless the ``MAILTRAP_TEST_*``
variables are set, so the default suite never touches the network:

    MAILTRAP_TEST_TOKEN=...                    # Mailtrap sending API token
    MAILTRAP_TEST_FROM=noreply@your-domain.es  # address on a verified sending domain
    MAILTRAP_TEST_TO=you@politicalwatch.es     # where the test email lands
"""

import os

import pytest

from tipi_tasks.mail import mailtrap_email

pytestmark = pytest.mark.integration

REQUIRED = ("MAILTRAP_TEST_TOKEN", "MAILTRAP_TEST_FROM", "MAILTRAP_TEST_TO")


@pytest.mark.skipif(
    not all(os.environ.get(var) for var in REQUIRED),
    reason=f"set {', '.join(REQUIRED)} to run the live Mailtrap send test",
)
def test_mailtrap_email_is_accepted_by_mailtrap():
    mail_config = {
        "API": os.environ["MAILTRAP_TEST_TOKEN"],
        "NAME": "QHLD tasks test",
        "FROM": os.environ["MAILTRAP_TEST_FROM"],
    }

    response = mailtrap_email(
        [os.environ["MAILTRAP_TEST_TO"]],
        "[qhld-tasks] Prueba de envío con Mailtrap",
        "<p>Email de prueba enviado por {{ sender }}.</p>",
        mail_config,
        {"sender": "tests/integration/test_mail_send.py"},
    )

    assert response["success"] is True
    assert len(response["message_ids"]) == 1
