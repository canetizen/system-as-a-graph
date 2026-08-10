"""
Description: Directory service adapter authenticating operators against LDAP (EXT-IF-06).
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

import ldap3

from saag_vae_operations_panel.model.session import AuthenticatedUser, Authorization
from saag_vae_operations_panel.ports.directory_service import AuthenticationFailed

#: Where the directory lives and how an account maps onto a bind DN.
SERVER_SETTING = "LDAP_URL"
BIND_TEMPLATE_SETTING = "LDAP_BIND_DN_TEMPLATE"

#: Where group entries live, e.g. ``ou=groups,dc=saag,dc=local``. Groups are
#: searched by membership rather than read from the account's ``memberOf``,
#: because that attribute only exists where the directory was configured to
#: maintain it. Unset falls back to ``memberOf`` for directories that do.
GROUP_SEARCH_BASE_SETTING = "LDAP_GROUP_SEARCH_BASE"

#: Read-only account the group search binds as. Directories commonly let an
#: account read itself and nothing else, so searching groups as the operator
#: who just logged in returns nothing — not because they are in no group, but
#: because they may not look. Unset searches as the operator.
SERVICE_BIND_DN_SETTING = "LDAP_SERVICE_BIND_DN"
SERVICE_PASSWORD_SETTING = "LDAP_SERVICE_PASSWORD"

#: Which LDAP group grants which authorization, as
#: ``authorization=group,authorization=group``. Membership is the only thing
#: SaaG reads from the directory: it never stores authorizations itself, so
#: revoking access is a directory change and takes effect at the next login.
GROUP_MAP_SETTING = "LDAP_GROUP_AUTHORIZATIONS"

_DEFAULT_ATTRIBUTES = ("cn", "displayName", "memberOf")


class LdapDirectoryService:
    """Authenticates an operator by binding as them.

    A bind is the only honest test of a credential — asking the directory
    whether a password matches is not something LDAP offers, and doing the
    comparison here would mean holding the password hash. A refused bind is
    reported without saying why, so the answer cannot be used to enumerate
    accounts.
    """

    def __init__(
        self,
        server_url: str | None = None,
        bind_dn_template: str | None = None,
        group_search_base: str | None = None,
        service_bind_dn: str | None = None,
        service_password: str | None = None,
        group_authorizations: str | dict[str, set[Authorization]] | None = None,
    ) -> None:
        """Initialize the adapter.

        Every setting arrives here explicitly; the deployment's values reach this
        adapter through the CSU's declared component properties rather than being
        read from the environment where they happen to be needed (SDD §2.5). The
        module's ``*_SETTING`` constants name the settings an operator sets, and
        are quoted back in the error below.

        Args:
            server_url: LDAP URL.
            bind_dn_template: Template turning a username into a bind DN, e.g.
                ``uid={username},ou=people,dc=saag,dc=local``.
            group_search_base: Where to look for group entries.
            service_bind_dn: Read-only account the group search binds as.
            service_password: That account's password.
            group_authorizations: Group name to the authorizations it grants. One
                group may grant several, which is the ordinary case. Accepts the
                configured text form as well as an already-parsed mapping, so a
                deployment's single setting and a test's explicit mapping use the
                same argument.

        Raises:
            RuntimeError: If the server URL or bind template is not configured.
                A directory adapter that cannot say where the directory is would
                fail every login instead, which is harder to diagnose.
        """
        self._server_url = server_url or ""
        self._bind_dn_template = bind_dn_template or ""
        self._group_search_base = group_search_base or ""
        self._service_bind_dn = service_bind_dn or ""
        self._service_password = service_password or ""
        self._group_authorizations = (
            _parse_group_map(group_authorizations or "")
            if isinstance(group_authorizations, str) or group_authorizations is None
            else group_authorizations
        )

        if not self._server_url or not self._bind_dn_template:
            raise RuntimeError(
                f"{SERVER_SETTING} and {BIND_TEMPLATE_SETTING} must be set for "
                f"the operations panel to authenticate anyone"
            )

    def authenticate(self, username: str, password: str) -> AuthenticatedUser:
        """Bind as the operator and read back who they are.

        Args:
            username: Directory account name.
            password: The account's password.

        Returns:
            The authenticated operator with the authorizations their group
            membership grants.

        Raises:
            AuthenticationFailed: If the bind is refused or the directory
                cannot be reached.
        """
        if not username or not password:
            raise AuthenticationFailed("Authentication failed")

        distinguished_name = self._bind_dn_template.format(username=username)

        try:
            connection = ldap3.Connection(
                ldap3.Server(self._server_url, get_info=ldap3.NONE),
                user=distinguished_name,
                password=password,
                auto_bind=True,
                raise_exceptions=True,
            )
        except ldap3.core.exceptions.LDAPException as exc:
            raise AuthenticationFailed("Authentication failed") from exc

        try:
            entry = self._read(connection, distinguished_name)
            groups = self._groups_of(connection, distinguished_name) or entry.get(
                "memberOf", []
            )
        finally:
            connection.unbind()

        return AuthenticatedUser(
            username=username,
            display_name=entry.get("displayName") or entry.get("cn") or username,
            authorizations=self._authorizations(groups),
        )

    def _groups_of(
        self, connection: ldap3.Connection, distinguished_name: str
    ) -> list[str]:
        """Return the groups an account belongs to, searched by membership.

        Both membership attributes in common use are accepted, since which one
        a directory populates is a schema choice nobody deploying SaaG gets to
        make.
        """
        if not self._group_search_base:
            return []

        searcher, owned = self._searcher(connection)
        try:
            searcher.search(
                search_base=self._group_search_base,
                search_filter=(
                    f"(|(member={distinguished_name})(uniqueMember={distinguished_name}))"
                ),
                search_scope=ldap3.SUBTREE,
                attributes=["cn"],
            )
            return [str(entry.entry_dn) for entry in searcher.entries]
        except ldap3.core.exceptions.LDAPException:
            # A directory that will not show its groups grants no authorization
            # rather than refusing the login: the operator is who they say they
            # are, they simply may do nothing.
            return []
        finally:
            if owned:
                searcher.unbind()

    def _searcher(self, connection: ldap3.Connection) -> tuple[ldap3.Connection, bool]:
        """Return the connection to search groups with, and whether we own it."""
        if not self._service_bind_dn:
            return connection, False

        return (
            ldap3.Connection(
                ldap3.Server(self._server_url, get_info=ldap3.NONE),
                user=self._service_bind_dn,
                password=self._service_password,
                auto_bind=True,
                raise_exceptions=True,
            ),
            True,
        )

    def _read(self, connection: ldap3.Connection, distinguished_name: str) -> dict:
        """Read the account the caller just bound as.

        Read at its own distinguished name rather than searched for under a
        base: the bind already proved the entry exists and where it is, and a
        filtered search would need an attribute name the two big directory
        products disagree about.
        """
        connection.search(
            search_base=distinguished_name,
            search_filter="(objectClass=*)",
            search_scope=ldap3.BASE,
            attributes=list(_DEFAULT_ATTRIBUTES),
        )

        if not connection.entries:
            return {}

        attributes = connection.entries[0].entry_attributes_as_dict
        return {
            "cn": _first(attributes.get("cn")),
            "displayName": _first(attributes.get("displayName")),
            "memberOf": [str(value) for value in attributes.get("memberOf", [])],
        }

    def _authorizations(self, member_of: list[str]) -> frozenset[Authorization]:
        """Map the groups an account belongs to onto what it may do.

        A group is matched either by its full distinguished name or by its
        common name, so the mapping can be written the short way without
        knowing the directory's tree.
        """
        memberships = {value.lower() for value in member_of}
        common_names = {
            part.strip().lower()[len("cn=") :]
            for value in memberships
            for part in value.split(",")
            if part.strip().lower().startswith("cn=")
        }

        granted: set[Authorization] = set()
        for group, authorizations in self._group_authorizations.items():
            if group.lower() in memberships or group.lower() in common_names:
                granted.update(authorizations)
        return frozenset(granted)


def _first(values: list | None) -> str:
    return str(values[0]) if values else ""


def _parse_group_map(raw: str) -> dict[str, set[Authorization]]:
    """Parse ``authorization=group`` pairs into a lookup.

    Args:
        raw: Comma-separated pairs. The same group may appear more than once:
            one directory group commonly grants several authorizations, so the
            pairs accumulate rather than overwrite.

    Returns:
        Group name to the authorizations it grants; unknown authorization names
        are ignored rather than failing startup, since the directory is edited
        by people who do not deploy SaaG.
    """
    mapping: dict[str, set[Authorization]] = {}
    for pair in raw.split(","):
        if "=" not in pair:
            continue
        name, group = pair.split("=", 1)
        try:
            authorization = Authorization(name.strip())
        except ValueError:
            continue
        mapping.setdefault(group.strip(), set()).add(authorization)
    return mapping
