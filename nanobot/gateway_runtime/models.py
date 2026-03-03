"""Shared models for gateway runtime control plane."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class RuntimeMode(str, Enum):
    """Supported gateway runtime modes."""

    FOREGROUND_LEGACY = "foreground_legacy"
    BACKGROUND_MANAGED = "background_managed"


@dataclass(frozen=True)
class RuntimePolicy:
    """Resolved runtime policy for the current command execution."""

    mode: RuntimeMode
    reason: str
    platform: str
    rollout_stage: str


GatewayRuntimeState = dict[str, Any]


@dataclass(frozen=True)
class GatewayStartOptions:
    """Gateway start options shared between CLI and adapters."""

    port: int = 18790
    verbose: bool = False
    cli_mode: str | None = None


@dataclass(frozen=True)
class StartResult:
    """Result from runtime start operation."""

    started: bool
    message: str
    mode: RuntimeMode


@dataclass(frozen=True)
class RestartResult:
    """Result from runtime restart operation."""

    restarted: bool
    message: str
    mode: RuntimeMode


@dataclass(frozen=True)
class StopResult:
    """Result from runtime stop operation."""

    stopped: bool
    message: str
    mode: RuntimeMode


@dataclass(frozen=True)
class GatewayStatus:
    """Status payload exposed by runtime facade and adapters."""

    running: bool
    mode: RuntimeMode
    reason: str
    platform: str
    rollout_stage: str
    pid: int | None = None
    log_path: Path | None = None
