from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..fixtures.identities import Actor


class ResourceKind(StrEnum):
    PROPERTY = "property"
    INVOICE = "invoice"
    ADMIN_AUDIT = "admin_audit"


class Action(StrEnum):
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN_READ = "admin_read"


@dataclass(frozen=True, slots=True)
class AuthorizationCase:
    case_id: str
    actor: Actor
    resource: ResourceKind
    action: Action
    resource_owner: Actor | None
    resource_state: str
    expected_status: int
    allowed: bool
    expected_audit_action: str | None = None


AUTHORIZATION_CASES = (
    AuthorizationCase(
        "anonymous-read-draft-property",
        Actor.ANONYMOUS,
        ResourceKind.PROPERTY,
        Action.READ,
        Actor.USER_A,
        "draft",
        401,
        False,
    ),
    AuthorizationCase(
        "owner-read-own-draft-property",
        Actor.USER_A,
        ResourceKind.PROPERTY,
        Action.READ,
        Actor.USER_A,
        "draft",
        200,
        True,
    ),
    AuthorizationCase(
        "other-user-read-draft-property",
        Actor.USER_B,
        ResourceKind.PROPERTY,
        Action.READ,
        Actor.USER_A,
        "draft",
        404,
        False,
        "read",
    ),
    AuthorizationCase(
        "other-user-read-published-property",
        Actor.USER_A,
        ResourceKind.PROPERTY,
        Action.READ,
        Actor.USER_B,
        "published",
        404,
        False,
        "read",
    ),
    AuthorizationCase(
        "admin-read-draft-property",
        Actor.ADMIN,
        ResourceKind.PROPERTY,
        Action.READ,
        Actor.USER_A,
        "draft",
        200,
        True,
    ),
    AuthorizationCase(
        "owner-update-own-draft-property",
        Actor.USER_A,
        ResourceKind.PROPERTY,
        Action.UPDATE,
        Actor.USER_A,
        "draft",
        200,
        True,
    ),
    AuthorizationCase(
        "other-user-update-draft-property",
        Actor.USER_B,
        ResourceKind.PROPERTY,
        Action.UPDATE,
        Actor.USER_A,
        "draft",
        404,
        False,
        "update",
    ),
    AuthorizationCase(
        "admin-update-draft-property",
        Actor.ADMIN,
        ResourceKind.PROPERTY,
        Action.UPDATE,
        Actor.USER_A,
        "draft",
        200,
        True,
    ),
    AuthorizationCase(
        "owner-update-own-archived-property",
        Actor.USER_A,
        ResourceKind.PROPERTY,
        Action.UPDATE,
        Actor.USER_A,
        "archived",
        404,
        False,
        "update",
    ),
    AuthorizationCase(
        "admin-update-archived-property",
        Actor.ADMIN,
        ResourceKind.PROPERTY,
        Action.UPDATE,
        Actor.USER_A,
        "archived",
        200,
        True,
    ),
    AuthorizationCase(
        "other-user-delete-draft-property",
        Actor.USER_B,
        ResourceKind.PROPERTY,
        Action.DELETE,
        Actor.USER_A,
        "draft",
        404,
        False,
        "delete",
    ),
    AuthorizationCase(
        "owner-delete-own-draft-property",
        Actor.USER_A,
        ResourceKind.PROPERTY,
        Action.DELETE,
        Actor.USER_A,
        "draft",
        204,
        True,
    ),
    AuthorizationCase(
        "owner-delete-own-archived-property",
        Actor.USER_A,
        ResourceKind.PROPERTY,
        Action.DELETE,
        Actor.USER_A,
        "archived",
        404,
        False,
        "delete",
    ),
    AuthorizationCase(
        "admin-delete-archived-property",
        Actor.ADMIN,
        ResourceKind.PROPERTY,
        Action.DELETE,
        Actor.USER_A,
        "archived",
        204,
        True,
    ),
    AuthorizationCase(
        "admin-delete-published-property",
        Actor.ADMIN,
        ResourceKind.PROPERTY,
        Action.DELETE,
        Actor.USER_B,
        "published",
        204,
        True,
    ),
    AuthorizationCase(
        "owner-read-own-open-invoice",
        Actor.USER_A,
        ResourceKind.INVOICE,
        Action.READ,
        Actor.USER_A,
        "open",
        200,
        True,
    ),
    AuthorizationCase(
        "other-user-read-open-invoice",
        Actor.USER_B,
        ResourceKind.INVOICE,
        Action.READ,
        Actor.USER_A,
        "open",
        404,
        False,
        "read",
    ),
    AuthorizationCase(
        "admin-read-open-invoice",
        Actor.ADMIN,
        ResourceKind.INVOICE,
        Action.READ,
        Actor.USER_A,
        "open",
        200,
        True,
    ),
    AuthorizationCase(
        "ordinary-user-call-admin-function",
        Actor.USER_A,
        ResourceKind.ADMIN_AUDIT,
        Action.ADMIN_READ,
        None,
        "not_applicable",
        403,
        False,
        "get",
    ),
    AuthorizationCase(
        "admin-call-admin-function",
        Actor.ADMIN,
        ResourceKind.ADMIN_AUDIT,
        Action.ADMIN_READ,
        None,
        "not_applicable",
        200,
        True,
    ),
)
