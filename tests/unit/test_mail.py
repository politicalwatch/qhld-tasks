"""Unit tests for ``mailtrap_email``: the template is rendered and handed to the
Mailtrap SDK as a well-formed ``Mail``. ``MailtrapClient`` is mocked — no network."""

from unittest.mock import patch

import mailtrap as mt
import pytest

from tipi_tasks import mail

pytestmark = pytest.mark.unit

MAIL_CONFIG = {"API": "test-token", "NAME": "QHLD", "FROM": "noreply@quehacenlosdiputados.es"}
SEND_RESPONSE = {"success": True, "message_ids": ["0c7fd939-02cf-11ed-88c2-0a58a9feac02"]}


@pytest.fixture
def mailtrap_client():
    with patch.object(mail.mt, "MailtrapClient") as client_cls:
        client_cls.return_value.send.return_value = SEND_RESPONSE
        yield client_cls


def test_mailtrap_email_sends_rendered_template(mailtrap_client):
    result = mail.mailtrap_email(
        ["alex@politicalwatch.es"], "Asunto", "<p>Hola {{ name }}</p>", MAIL_CONFIG,
        {"name": "Alex"},
    )

    mailtrap_client.assert_called_once_with(token="test-token")
    mailtrap_client.return_value.send.assert_called_once()
    sent = mailtrap_client.return_value.send.call_args[0][0]
    assert isinstance(sent, mt.Mail)
    assert sent.sender == mt.Address(email="noreply@quehacenlosdiputados.es", name="QHLD")
    assert sent.to == [mt.Address(email="alex@politicalwatch.es")]
    assert sent.subject == "Asunto"
    assert sent.html == "<p>Hola Alex</p>"
    assert result == SEND_RESPONSE


def test_mailtrap_email_propagates_api_errors(mailtrap_client):
    mailtrap_client.return_value.send.side_effect = mt.APIError(401, ["Unauthorized"])

    with pytest.raises(mt.APIError):
        mail.mailtrap_email(["a@x.es"], "Asunto", "<p></p>", MAIL_CONFIG)


def test_send_email_uses_mailtrap_outside_debug(monkeypatch, mailtrap_client):
    monkeypatch.setattr(mail.config, "DEBUG", False)

    assert mail.send_email(["a@x.es"], "Asunto", "<p></p>", MAIL_CONFIG) == SEND_RESPONSE
    mailtrap_client.return_value.send.assert_called_once()


def test_send_email_only_prints_in_debug(monkeypatch, mailtrap_client):
    monkeypatch.setattr(mail.config, "DEBUG", True)

    mail.send_email(["a@x.es"], "Asunto", "<p></p>", MAIL_CONFIG)
    mailtrap_client.assert_not_called()
