"""
Description: TC-VAE01-01 — Session & Authentication Manager (SRS VAE-01.3-4).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from saag_contracts.types.identifiers import system_version
from saag_vae_operations_panel.adapters.jwt_tokens import JwtTokenService
from saag_vae_operations_panel.model.session import Authorization
from saag_vae_operations_panel.ports.directory_service import AuthenticationFailed
from saag_vae_operations_panel.testing.panel import (
    EFFECTIVE_VERSION,
    OLDER_VERSION,
    PLATFORM,
    PROJECT,
    FixedClock,
)
from saag_vae_operations_panel.use_cases.manage_session import NotAuthorized


def test_valid_credentials_grant_access_within_their_authorizations(panel):
    """A known operator is admitted, carrying what they are allowed to do."""
    granted = panel.log_in("operator", "operator")

    assert granted.token
    assert granted.session.user.username == "operator"
    assert granted.session.user.may(Authorization.PRODUCE_MODEL_SETUP_DATA)
    assert not granted.session.is_expired(panel.clock.now())


def test_invalid_credentials_are_denied(panel):
    """A wrong password and an unknown account are both refused."""
    with pytest.raises(AuthenticationFailed):
        panel.log_in("operator", "wrong-password")

    with pytest.raises(AuthenticationFailed):
        panel.log_in("nobody", "whatever")


def test_authentication_alone_does_not_grant_every_operation(panel):
    """VAE-01.3 admits users only within the scope of their authorizations."""
    granted = panel.log_in("viewer", "viewer")

    assert panel.session.authorize(granted.token, Authorization.VIEW)

    with pytest.raises(NotAuthorized):
        panel.session.authorize(
            granted.token, Authorization.PRODUCE_MODEL_SETUP_DATA
        )


def test_a_tampered_or_foreign_token_is_refused(panel):
    """A token this service did not sign is not a session."""
    granted = panel.log_in()
    forged = JwtTokenService(
        clock=panel.clock,
        lifetime=timedelta(hours=8),
        secret="another-secret-long-enough-for-hmac-sha256",
    ).issue(granted.session.user)[0]

    with pytest.raises(AuthenticationFailed):
        panel.session.authorize(forged, Authorization.VIEW)

    with pytest.raises(AuthenticationFailed):
        panel.session.authorize(granted.token + "x", Authorization.VIEW)


def test_an_expired_session_is_refused(panel):
    """A session stops working once its lifetime is over."""
    granted = panel.log_in()
    panel.session._clock = FixedClock(
        panel.clock.now() + timedelta(days=1)
    )

    with pytest.raises(AuthenticationFailed):
        panel.session.authorize(granted.token, Authorization.VIEW)


def test_selecting_a_scope_marks_whether_it_is_the_effective_version(panel):
    """The effective version is reported distinctly from the selected one."""
    panel.log_in()

    selected = panel.session.select(
        "operator", system_version(PROJECT, PLATFORM, EFFECTIVE_VERSION)
    )
    assert selected.selected_is_effective is True

    older = panel.session.select("operator", system_version(PROJECT, PLATFORM, OLDER_VERSION))
    assert older.selected_is_effective is False
    assert panel.session.list_versions(PROJECT, PLATFORM).effective_version.version == (
        EFFECTIVE_VERSION
    )


def test_the_selection_is_remembered_per_operator(panel):
    """Two operators may work on different versions at the same time."""
    panel.session.select("operator", system_version(PROJECT, PLATFORM, EFFECTIVE_VERSION))
    panel.session.select("viewer", system_version(PROJECT, PLATFORM, OLDER_VERSION))

    assert panel.session.current("operator").system_version.version == EFFECTIVE_VERSION
    assert panel.session.current("viewer").system_version.version == OLDER_VERSION
    assert panel.session.current("someone-else") is None
