from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..config import SecurityTestSettings


class Actor(StrEnum):
    ANONYMOUS = "anonymous"
    USER_A = "userA"
    USER_B = "userB"
    ADMIN = "admin"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Credentials:
    actor: Actor
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class IdentityCatalog:
    user_a: Credentials
    user_b: Credentials
    admin: Credentials
    unknown: Credentials

    @classmethod
    def from_settings(cls, settings: SecurityTestSettings) -> IdentityCatalog:
        return cls(
            user_a=Credentials(
                actor=Actor.USER_A,
                email=settings.user_a_email,
                password=settings.user_a_password,
            ),
            user_b=Credentials(
                actor=Actor.USER_B,
                email=settings.user_b_email,
                password=settings.user_b_password,
            ),
            admin=Credentials(
                actor=Actor.ADMIN,
                email=settings.admin_email,
                password=settings.admin_password,
            ),
            unknown=Credentials(
                actor=Actor.UNKNOWN,
                email=settings.unknown_email,
                password=settings.replacement_password,
            ),
        )

    def for_actor(self, actor: Actor) -> Credentials:
        identities = {
            Actor.USER_A: self.user_a,
            Actor.USER_B: self.user_b,
            Actor.ADMIN: self.admin,
            Actor.UNKNOWN: self.unknown,
        }
        try:
            return identities[actor]
        except KeyError as error:
            raise ValueError(f"Actor {actor.value} has no credentials") from error
