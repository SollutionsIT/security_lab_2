from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from .identities import Actor

type JsonObject = dict[str, Any]


def _object(value: object, label: str) -> JsonObject:
    if not isinstance(value, dict):
        raise AssertionError(f"{label} must be a JSON object")
    return cast(JsonObject, value)


def _list_of_objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or not all(isinstance(entry, dict) for entry in value):
        raise AssertionError(f"{label} must be a list of JSON objects")
    return cast(list[JsonObject], value)


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssertionError(f"{label} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class SeedAlias:
    user_id: str
    property_id: str | None = None
    invoice_id: str | None = None


@dataclass(frozen=True, slots=True)
class SeedResources:
    user_a: SeedAlias
    user_b: SeedAlias
    admin: SeedAlias

    @classmethod
    def from_state(cls, state: JsonObject) -> SeedResources:
        aliases = _object(state.get("seedAliases"), "state.seedAliases")

        def parse(name: str, *, owns_resources: bool) -> SeedAlias:
            value = _object(aliases.get(name), f"state.seedAliases.{name}")
            return SeedAlias(
                user_id=_required_string(value.get("userId"), f"{name}.userId"),
                property_id=(
                    _required_string(value.get("propertyId"), f"{name}.propertyId")
                    if owns_resources
                    else None
                ),
                invoice_id=(
                    _required_string(value.get("invoiceId"), f"{name}.invoiceId")
                    if owns_resources
                    else None
                ),
            )

        return cls(
            user_a=parse("userA", owns_resources=True),
            user_b=parse("userB", owns_resources=True),
            admin=parse("admin", owns_resources=False),
        )

    def for_actor(self, actor: Actor) -> SeedAlias:
        aliases = {
            Actor.USER_A: self.user_a,
            Actor.USER_B: self.user_b,
            Actor.ADMIN: self.admin,
        }
        try:
            return aliases[actor]
        except KeyError as error:
            raise ValueError(f"Actor {actor.value} has no seed alias") from error


def property_from_state(state: JsonObject, property_id: str) -> JsonObject | None:
    properties = _list_of_objects(state.get("properties"), "state.properties")
    return next((entry for entry in properties if entry.get("id") == property_id), None)


def invoice_from_state(state: JsonObject, invoice_id: str) -> JsonObject | None:
    invoices = _list_of_objects(state.get("invoices"), "state.invoices")
    return next((entry for entry in invoices if entry.get("id") == invoice_id), None)


def webhook_events_from_state(state: JsonObject) -> list[JsonObject]:
    return _list_of_objects(state.get("webhookEvents"), "state.webhookEvents")


def event_list(payload: JsonObject) -> list[JsonObject]:
    return _list_of_objects(payload.get("events"), "events")


def message_list(payload: JsonObject) -> list[JsonObject]:
    return _list_of_objects(payload.get("messages"), "messages")
