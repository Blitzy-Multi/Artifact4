"""Flask extension singletons, wired to the app in the factory via init_app().

Baseline: the original Node.js source is absent, so no extensions are required
and register_extensions is a safe no-op that establishes the wiring seam.
Conditional extensions (e.g., CORS, SQLAlchemy) are instantiated unbound here
and bound inside register_extensions ONLY when the original exercises them.
"""


def register_extensions(app):
    """Bind Flask extensions to the application. Baseline no-op."""
    return None
