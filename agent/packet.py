"""The launch packet: its schema, its validation and its deterministic audit.

The model writes the packet; this module decides what it is allowed to claim.
A "sourced" item keeps that label only if its URL is http(s) and resolves.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

Packet = dict[str, Any]
UrlCheck = Callable[[str], bool]

OWNERS = ("agent", "ceo", "professional")
STATUSES = ("drafted", "needs_decision", "needs_professional")
CONFIDENCES = ("sourced", "unverified")
SOURCED_SECTIONS = ("compliance", "funding")


class PacketError(ValueError):
    """The packet does not have the shape the page and the audit rely on."""


def _obj(**props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _arr(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


def _enum(values: tuple[str, ...]) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


_STR = {"type": "string"}

PACKET_SCHEMA: dict[str, Any] = _obj(
    company=_obj(name=_STR, one_liner=_STR, sector=_STR, jurisdiction=_STR),
    stages=_arr(
        _obj(
            name=_STR,
            goal=_STR,
            exit_criteria=_STR,
            tasks=_arr(_obj(title=_STR, owner=_enum(OWNERS), status=_enum(STATUSES))),
        )
    ),
    compliance=_arr(_obj(item=_STR, why=_STR, when=_STR, source_url=_STR, confidence=_enum(CONFIDENCES))),
    hires=_arr(_obj(role=_STR, stage=_STR, why=_STR)),
    funding=_arr(_obj(name=_STR, type=_STR, why_fit=_STR, source_url=_STR, confidence=_enum(CONFIDENCES))),
    decisions=_arr(_obj(id=_STR, question=_STR, options=_arr(_STR), recommended=_STR, why=_STR)),
    drafts=_arr(_obj(title=_STR, kind=_STR, body=_STR)),
    limits=_arr(_STR),
)


def _check(node: Any, schema: dict[str, Any], path: str) -> None:
    kind = schema["type"]
    if kind == "object":
        if not isinstance(node, dict):
            raise PacketError(f"{path}: expected an object")
        for key, child in schema["properties"].items():
            if key not in node:
                raise PacketError(f"{path}: missing '{key}'")
            _check(node[key], child, f"{path}.{key}")
    elif kind == "array":
        if not isinstance(node, list):
            raise PacketError(f"{path}: expected a list")
        for index, item in enumerate(node):
            _check(item, schema["items"], f"{path}[{index}]")
    else:
        if not isinstance(node, str):
            raise PacketError(f"{path}: expected text")
        if "enum" in schema and node not in schema["enum"]:
            raise PacketError(f"{path}: '{node}' is not one of {schema['enum']}")


def validate(packet: Packet) -> None:
    """Raise PacketError unless the packet matches the schema and its decisions are answerable."""
    _check(packet, PACKET_SCHEMA, "packet")
    ids = [decision["id"] for decision in packet["decisions"]]
    if len(set(ids)) != len(ids):
        raise PacketError("decisions: duplicate ids, so a saved choice could not be told apart")
    for decision in packet["decisions"]:
        where = f"decision '{decision['id']}'"
        if len(decision["options"]) < 2:
            raise PacketError(f"{where}: needs at least two options")
        if decision["recommended"] not in decision["options"]:
            raise PacketError(f"{where}: recommended is not one of its options")


def is_http_url(url: str) -> bool:
    return url.startswith(("https://", "http://")) and len(url) < 2000 and " " not in url


def _audit_item(item: dict[str, Any], url_ok: UrlCheck) -> dict[str, Any]:
    url = item["source_url"].strip()
    if not is_http_url(url):
        return {**item, "source_url": "", "confidence": "unverified"}
    if item["confidence"] == "sourced" and not url_ok(url):
        return {**item, "source_url": url, "confidence": "unverified"}
    return {**item, "source_url": url}


def audit(packet: Packet, url_ok: UrlCheck) -> tuple[Packet, dict[str, Any]]:
    """Return a new packet with unsupported "sourced" labels downgraded, plus a report.

    The input is never modified.
    """
    audited = copy.deepcopy(packet)
    claimed = verified = 0
    for section in SOURCED_SECTIONS:
        claimed += sum(1 for item in packet[section] if item["confidence"] == "sourced")
        audited[section] = [_audit_item(item, url_ok) for item in packet[section]]
        verified += sum(1 for item in audited[section] if item["confidence"] == "sourced")

    tasks = [task for stage in audited["stages"] for task in stage["tasks"]]
    workload = {owner: sum(1 for task in tasks if task["owner"] == owner) for owner in OWNERS}
    report = {
        "sources": {"claimed": claimed, "verified": verified, "downgraded": claimed - verified},
        "workload": {**workload, "total": len(tasks)},
        "decisions": len(audited["decisions"]),
    }
    return audited, report
