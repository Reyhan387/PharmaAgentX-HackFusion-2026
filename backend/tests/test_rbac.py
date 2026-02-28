# backend/tests/test_rbac.py
# Tests for Step 49 — Role-Based Access Control (RBAC) Hardening

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from backend.app.core.rbac import RBACService


def _make_user(role: str):
    user = MagicMock()
    user.role = role
    return user


def _make_db():
    db = MagicMock()
    return db


class TestRBACServiceRequireRole:

    def test_allowed_role_returns_none(self):
        user = _make_user("admin")
        db = _make_db()
        result = RBACService.require_role(user, ["admin"], db)
        assert result is None

    def test_allowed_role_among_multiple_returns_none(self):
        user = _make_user("system")
        db = _make_db()
        result = RBACService.require_role(user, ["admin", "system"], db)
        assert result is None

    def test_allowed_role_does_not_write_to_db(self):
        user = _make_user("admin")
        db = _make_db()
        RBACService.require_role(user, ["admin"], db)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_disallowed_role_raises_403(self):
        user = _make_user("patient")
        db = _make_db()
        with pytest.raises(HTTPException) as exc_info:
            RBACService.require_role(user, ["admin"], db)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Insufficient permissions"

    def test_disallowed_role_logs_denial_to_db(self):
        user = _make_user("patient")
        db = _make_db()
        with pytest.raises(HTTPException):
            RBACService.require_role(user, ["admin"], db)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_denial_log_contains_correct_event_type(self):
        user = _make_user("patient")
        db = _make_db()
        with pytest.raises(HTTPException):
            RBACService.require_role(user, ["admin"], db)
        audit_log = db.add.call_args[0][0]
        assert audit_log.event_type == "ACCESS_DENIED"

    def test_denial_log_actor_is_user_role(self):
        user = _make_user("patient")
        db = _make_db()
        with pytest.raises(HTTPException):
            RBACService.require_role(user, ["admin"], db)
        audit_log = db.add.call_args[0][0]
        assert audit_log.actor == "patient"

    def test_empty_allowed_roles_denies_any_user(self):
        user = _make_user("admin")
        db = _make_db()
        with pytest.raises(HTTPException) as exc_info:
            RBACService.require_role(user, [], db)
        assert exc_info.value.status_code == 403
