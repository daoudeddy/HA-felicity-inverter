from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import re
from typing import Any

from .protocol import POLL_COMMANDS

_LOGGER = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 0.5
_MAX_READ_ITERATIONS = 20


class FelicityApiError(Exception):
    """Error while communicating with a Felicity inverter."""


@dataclass(slots=True)
class ParsedResponse:
    """Structured response for a single inverter command."""

    command: str
    raw: str | None
    objects: list[dict[str, Any]]


@dataclass(slots=True)
class RawPollData:
    """All raw responses collected during a polling cycle."""

    responses: dict[str, ParsedResponse]


class FelicityClient:
    """TCP client for the Felicity WiFi telemetry interface."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    async def async_fetch_data(self) -> RawPollData:
        """Poll inverter TCP telemetry and return raw structured responses."""
        responses: dict[str, ParsedResponse] = {}

        responses["real"] = await self._async_fetch_command(POLL_COMMANDS["real"])
        if not responses["real"].objects:
            raise FelicityApiError("Runtime telemetry response did not contain valid JSON objects")

        for key in ("basic", "set"):
            command = POLL_COMMANDS[key]
            try:
                responses[key] = await self._async_fetch_command(command)
            except FelicityApiError as err:
                _LOGGER.debug("Optional command %s failed: %s", command, err)
                responses[key] = ParsedResponse(command=command, raw=None, objects=[])

        return RawPollData(responses=responses)

    async def _async_fetch_command(self, command: str) -> ParsedResponse:
        raw = await self._async_read_raw(command)
        objects = split_json_objects(raw)
        return ParsedResponse(command=command, raw=raw, objects=objects)

    async def _async_read_raw(self, command: str) -> str:
        """Open a TCP socket, send a command, and return the raw response text."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=_CONNECT_TIMEOUT,
            )
        except Exception as err:
            raise FelicityApiError(
                f"Error connecting to {self._host}:{self._port}: {err}"
            ) from err

        try:
            writer.write(command.encode("ascii") + b"\n")
            await writer.drain()

            chunks: list[bytes] = []
            for _ in range(_MAX_READ_ITERATIONS):
                try:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=_READ_TIMEOUT)
                except asyncio.TimeoutError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
        except Exception as err:
            raise FelicityApiError(
                f"Error talking to {self._host}:{self._port}: {err}"
            ) from err
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

        if not chunks:
            raise FelicityApiError("No data received from inverter")

        raw = b"".join(chunks).decode("utf-8", errors="ignore").strip()
        _LOGGER.debug("Raw Felicity response for %s: %r", command, raw)
        return raw


def split_json_objects(raw: str) -> list[dict[str, Any]]:
    """Split concatenated JSON objects using brace depth and parse them."""
    normalized = _normalize_payload(raw)
    objects: list[dict[str, Any]] = []
    block: list[str] = []
    depth = 0
    in_string = False
    escape = False

    for char in normalized:
        if depth == 0 and char != "{":
            continue

        if char == '"' and not escape:
            in_string = not in_string

        if char == "\\" and in_string and not escape:
            escape = True
        else:
            escape = False

        if char == "{" and not in_string:
            depth += 1

        if depth > 0:
            block.append(char)

        if char == "}" and not in_string and depth > 0:
            depth -= 1
            if depth == 0 and block:
                candidate = "".join(block)
                block = []
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError as err:
                    _LOGGER.debug("Skipping invalid JSON chunk %r: %s", candidate, err)
                    continue
                if isinstance(parsed, dict):
                    objects.append(parsed)

    return objects


def merge_json_objects(objects: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge parsed JSON objects using last-write-wins updates."""
    merged: dict[str, Any] = {}
    for obj in objects:
        if isinstance(obj, dict):
            merged.update(obj)
    return merged


def _normalize_payload(raw: str) -> str:
    """Normalize slightly malformed JSON-ish payloads to valid JSON."""
    normalized = raw.strip().replace("\r", "").replace("\n", "")
    normalized = normalized.replace("'", '"')
    normalized = re.sub(r"\bNone\b", "null", normalized)
    return normalized
