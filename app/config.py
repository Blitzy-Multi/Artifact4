"""Environment-driven configuration classes for the Flask application.

Values are read from the environment (loaded via python-dotenv at process
start) with safe defaults so the app can boot without a .env file. Secrets are
NEVER hard-coded beyond a development placeholder.
"""
import os

# Recognized string spellings for boolean environment variables. Parsing is
# case-insensitive and tolerant of surrounding whitespace.
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def parse_bool(value, default=None):
    """Parse a boolean from an environment-variable string.

    Accepts the common truthy/falsey spellings (case-insensitive,
    whitespace-tolerant): ``1/true/yes/on`` -> ``True`` and
    ``0/false/no/off`` -> ``False``.

    Args:
        value: The raw string (typically from :func:`os.getenv`) or ``None``.
        default: Value returned when ``value`` is ``None`` or unrecognized.

    Returns:
        The parsed boolean, or ``default`` when the input is absent or not a
        recognized boolean spelling. This lets callers distinguish "no override
        supplied" (``default=None``) from an explicit ``True``/``False``.
    """
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = False
    TESTING = False
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # Desired JSON key ordering for response parity. NOTE: in Flask 3.x the
    # standalone ``JSON_SORT_KEYS`` config key is inert; create_app() applies
    # this value to the active JSON provider via ``app.json.sort_keys`` so the
    # unsorted-key behavior is actually honored. Kept here as the single source
    # of truth for the setting.
    JSON_SORT_KEYS = False
    # Force compact JSON serialization in EVERY environment. Flask's default
    # JSON provider leaves ``compact`` unset (``None``), which makes it
    # pretty-print (indent=2) whenever ``app.debug`` is true and emit compact
    # output otherwise -- so the same endpoint would serialize differently in a
    # debug dev server versus production. Pinning this to ``True`` guarantees a
    # byte-identical response body across dev and prod (AAP §0.7 rule R6,
    # runtime dev/prod parity). create_app() applies it via ``app.json.compact``.
    JSON_COMPACT = True


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

DEFAULT_CONFIG = "development"


def get_config(config=None):
    """Resolve a configuration object from several input forms.

    None         -> APP_CONFIG env var, else DEFAULT_CONFIG ("development")
    str (name)   -> config_by_name lookup; unknown names fall back to default
    class/object -> passthrough (already a config)
    """
    if config is not None and not isinstance(config, str):
        return config

    name = config
    if name is None:
        name = os.getenv("APP_CONFIG") or DEFAULT_CONFIG

    return config_by_name.get(name, config_by_name[DEFAULT_CONFIG])
