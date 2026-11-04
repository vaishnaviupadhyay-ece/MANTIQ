"""
MANTIQ demo authentication.

"""

import hmac
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from app.config import DEMO_USERS, ROLE_LABELS

SESSION_KEY = "username"


@dataclass(frozen=True)
class User:
    username: str
    display_name: str
    role: str

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)


def _build_user(username: str) -> Optional[User]:
    info = DEMO_USERS.get(username)
    if info is None:
        return None
    return User(username=username, display_name=info["display_name"], role=info["role"])


def authenticate(username: str, password: str) -> Optional[User]:
    """Return the User if the credentials match, otherwise None."""
    username = (username or "").strip().lower()
    info = DEMO_USERS.get(username)
    if info is None:
        return None
    given = str(password or "").encode("utf-8")
    expected = info["password"].encode("utf-8")
    if not hmac.compare_digest(given, expected):
        return None
    return _build_user(username)


def login(user: User) -> None:
    st.session_state[SESSION_KEY] = user.username


def logout() -> None:
    st.session_state.pop(SESSION_KEY, None)


def current_user() -> Optional[User]:
    """The logged-in user, rebuilt from config on every call (so the role
    always comes from config.py, never from something stored in the session)."""
    username = st.session_state.get(SESSION_KEY)
    return _build_user(username) if username else None


def require_role(user: Optional[User], *allowed_roles: str) -> None:
    """Raise PermissionError unless the user has one of the allowed roles.
    The alert service will call this before every protected action."""
    if user is None or user.role not in allowed_roles:
        raise PermissionError("You do not have permission to perform this action.")