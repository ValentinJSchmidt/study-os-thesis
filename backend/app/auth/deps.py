"""Backward-compatible re-exports.

Authentication dependencies now live in ``app.dependencies`` (the central DI
module).  This file re-exports them so that any remaining imports from
``app.auth.deps`` continue to work.
"""

from app.dependencies import (  # noqa: F401
    CurrentUserDep,
    get_current_user,
    oauth2_scheme,
    require_role,
)
