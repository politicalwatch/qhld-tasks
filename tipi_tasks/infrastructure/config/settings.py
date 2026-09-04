"""Consolidated environment configuration as a single Pydantic ``Settings``.

Replaces the old hand-rolled ``tipi_tasks.config`` (module-level ``os.environ``
reads, manual ``int()`` coercion and a ``mail_config()`` that built a dict by
concatenating brand prefixes onto uppercase field names). Access it through the
memoised ``get_settings()`` / ``get_mail_settings()``.

Env var names are unchanged — they are a cross-repo contract shared with
``qhld-infra``'s ``.env.tasks``. Only fields something actually reads are kept:
``ALERT_BANNER_URL`` and ``CACHE_REDIS_DB_NAME``/``_HOST``/``_PORT`` had no
consumer anywhere and were set by no env file, so they were dropped in the
migration (their names did not even match the backend's ``CACHE_REDIS_*``).
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    # Celery. DEBUG also decides whether mail is sent or printed (see mail.py).
    # The old code compared the raw string against 'True', so DEBUG=true meant
    # False; pydantic accepts the usual truthy spellings. Every env we ship sets
    # DEBUG=False, so no deployment changes behaviour.
    debug: bool = False
    broker: str = "redis://redis:6379/2"
    result_backend: str = "redis://redis:6379/3"

    # Email templates. Empty means the ones packaged in tipi_tasks/templates.
    template_dir: str = ""

    # Days a search may stay unvalidated before its email is dropped.
    validation_timeout: int = 30
    # How often the clean-emails / clean-past-dates beat tasks run, in seconds.
    clean_emails_timeout: int = 300

    scanned_text_excerpt_size: int = 500


class MailSettings(BaseSettings):
    """One brand's mail identity: the ``TIPI_*``/``P2030_*``/``SCANNER_*`` block.

    Never instantiated directly — use the prefixed subclasses below.
    """

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    name: str = ""
    description: str = ""
    email: str = ""
    frontend: str = ""
    backend: str = ""
    color: str = ""
    api: str = ""
    banner_url: str = ""
    alert_subject: str = ""
    validation_subject: str = ""
    # The ``<PREFIX>FROM`` address. ``from`` is a keyword, so the field cannot be
    # named after its env var, and pydantic-settings ignores ``env_prefix`` for any
    # field carrying an alias — which is why each subclass has to repeat this one
    # field with its own absolute alias instead of inheriting it.
    sender: str = ""


class TipiMailSettings(MailSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore", env_prefix="TIPI_"
    )

    sender: str = Field("", validation_alias="TIPI_FROM")


class P2030MailSettings(MailSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore", env_prefix="P2030_"
    )

    sender: str = Field("", validation_alias="P2030_FROM")


class ScannerMailSettings(MailSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore", env_prefix="SCANNER_"
    )

    sender: str = Field("", validation_alias="SCANNER_FROM")


_MAIL_SETTINGS_BY_KNOWLEDGEBASE = {
    "politicas": TipiMailSettings,
    "ods": P2030MailSettings,
    "escaner": ScannerMailSettings,
}


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_mail_settings(knowledgebase: str) -> MailSettings:
    """The mail identity for a knowledgebase. Raises ``KeyError`` for an unknown
    one, as the dict-building version did."""
    return _MAIL_SETTINGS_BY_KNOWLEDGEBASE[knowledgebase]()
