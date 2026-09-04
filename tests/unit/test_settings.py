"""Unit tests for the consolidated Pydantic ``Settings`` — no infrastructure.

Pin the typed coercion the migration introduces: env vars are always strings, so
these assert booleans and ints are parsed rather than left as truthy strings.
``_env_file=None`` keeps these from reading the repo-root ``.env``; it does not
stop pydantic-settings reading ``os.environ``, hence the ``delenv`` calls.
"""

import pytest

from tipi_tasks.infrastructure.config.settings import (
    P2030MailSettings,
    ScannerMailSettings,
    Settings,
    TipiMailSettings,
    get_mail_settings,
)

pytestmark = pytest.mark.unit

_MAIL_FIELDS = (
    "NAME",
    "DESCRIPTION",
    "EMAIL",
    "FRONTEND",
    "BACKEND",
    "COLOR",
    "API",
    "BANNER_URL",
    "ALERT_SUBJECT",
    "VALIDATION_SUBJECT",
    "FROM",
)


@pytest.mark.parametrize("raw", ["False", "false", "0", "no", "off"])
def test_debug_falsey_strings_are_false(raw):
    assert Settings(_env_file=None, debug=raw).debug is False


@pytest.mark.parametrize("raw", ["True", "true", "1", "yes", "on"])
def test_debug_truthy_strings_are_true(raw):
    # The old config was ``env.get('DEBUG', 'False') == 'True'``, so DEBUG=true
    # meant *False* and mail went out where a debug print was intended. Every env
    # we ship sets DEBUG=False, so nothing deployed changes — pin it anyway.
    assert Settings(_env_file=None, debug=raw).debug is True


def test_int_fields_coerced():
    settings = Settings(
        _env_file=None,
        validation_timeout="5",
        clean_emails_timeout="60",
        scanned_text_excerpt_size="500",
    )
    assert settings.validation_timeout == 5
    assert settings.clean_emails_timeout == 60
    assert settings.scanned_text_excerpt_size == 500


def test_defaults(monkeypatch):
    for key in (
        "DEBUG",
        "BROKER",
        "RESULT_BACKEND",
        "TEMPLATE_DIR",
        "VALIDATION_TIMEOUT",
        "CLEAN_EMAILS_TIMEOUT",
        "SCANNED_TEXT_EXCERPT_SIZE",
    ):
        monkeypatch.delenv(key, raising=False)
    settings = Settings(_env_file=None)
    assert settings.debug is False
    assert settings.broker == "redis://redis:6379/2"
    assert settings.result_backend == "redis://redis:6379/3"
    # Empty means "use the templates packaged with tipi_tasks".
    assert settings.template_dir == ""
    assert settings.validation_timeout == 30
    assert settings.clean_emails_timeout == 300
    assert settings.scanned_text_excerpt_size == 500


@pytest.mark.parametrize(
    ("settings_class", "prefix"),
    [
        (TipiMailSettings, "TIPI_"),
        (P2030MailSettings, "P2030_"),
        (ScannerMailSettings, "SCANNER_"),
    ],
)
def test_mail_settings_read_their_own_prefix(settings_class, prefix, monkeypatch):
    """Each brand reads only its own block, ``FROM`` included. ``sender`` is the one
    field that cannot inherit the prefix (``from`` is a keyword, and an aliased field
    ignores ``env_prefix``), so it is the one that could silently read nothing."""
    for other in ("TIPI_", "P2030_", "SCANNER_"):
        for field in _MAIL_FIELDS:
            monkeypatch.setenv(other + field, f"{other}{field}-value")

    settings = settings_class(_env_file=None)

    assert settings.name == f"{prefix}NAME-value"
    assert settings.description == f"{prefix}DESCRIPTION-value"
    assert settings.email == f"{prefix}EMAIL-value"
    assert settings.frontend == f"{prefix}FRONTEND-value"
    assert settings.backend == f"{prefix}BACKEND-value"
    assert settings.color == f"{prefix}COLOR-value"
    assert settings.api == f"{prefix}API-value"
    assert settings.banner_url == f"{prefix}BANNER_URL-value"
    assert settings.alert_subject == f"{prefix}ALERT_SUBJECT-value"
    assert settings.validation_subject == f"{prefix}VALIDATION_SUBJECT-value"
    assert settings.sender == f"{prefix}FROM-value"


def test_mail_settings_default_to_empty_strings(monkeypatch):
    for field in _MAIL_FIELDS:
        monkeypatch.delenv("TIPI_" + field, raising=False)
    assert TipiMailSettings(_env_file=None).model_dump() == {
        field: "" for field in TipiMailSettings.model_fields
    }


@pytest.mark.parametrize(
    ("knowledgebase", "settings_class"),
    [
        ("politicas", TipiMailSettings),
        ("ods", P2030MailSettings),
        ("escaner", ScannerMailSettings),
    ],
)
def test_get_mail_settings_maps_each_knowledgebase(knowledgebase, settings_class):
    assert isinstance(get_mail_settings(knowledgebase), settings_class)


def test_get_mail_settings_rejects_an_unknown_knowledgebase():
    # The dict-building version raised KeyError too; keep that contract.
    with pytest.raises(KeyError):
        get_mail_settings("nope")
