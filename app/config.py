"""Environment-driven configuration classes for the Flask application.

Values are read from the environment (loaded via python-dotenv at process
start) with safe defaults so the app can boot without a .env file. Secrets are
NEVER hard-coded beyond a development placeholder.
"""
import os


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = False
    TESTING = False
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    JSON_SORT_KEYS = False


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
