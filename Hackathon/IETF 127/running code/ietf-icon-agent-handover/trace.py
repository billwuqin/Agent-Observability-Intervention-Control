"""Append-only trajectory. Bundle secrets are removed before an event is stored."""

from __future__ import annotations

SECRET_KEYS = {"subscriber_id", "raw_key", "playback_url"}
SECRET_MARK = "user-1001"


def redact(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key in SECRET_KEYS:
                cleaned[key] = "[redacted]"
            else:
                cleaned[key] = redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    if isinstance(value, str) and SECRET_MARK in value:
        return "[redacted]"
    return value


class Trace:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def add(self, event_type: str, **fields) -> None:
        payload = {"event_type": event_type, "sequence": len(self.events) + 1}
        payload.update(fields)
        self.events.append(redact(payload))
