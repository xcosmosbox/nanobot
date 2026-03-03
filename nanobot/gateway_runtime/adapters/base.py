"""Runtime adapter contract for gateway execution backends."""

from typing import Protocol

from nanobot.gateway_runtime.models import (
    GatewayStartOptions,
    GatewayStatus,
    RestartResult,
    StartResult,
    StopResult,
)


class RuntimeAdapter(Protocol):
    """Adapter protocol for gateway runtime operations."""

    def start(self, options: GatewayStartOptions) -> StartResult:
        """Start gateway runtime."""

    def stop(self, timeout_s: int = 20) -> StopResult:
        """Stop gateway runtime."""

    def restart(self, options: GatewayStartOptions, timeout_s: int = 20) -> RestartResult:
        """Restart gateway runtime."""

    def status(self) -> GatewayStatus:
        """Get gateway runtime status."""

    def logs(self, follow: bool = True, tail: int = 200) -> int:
        """Show runtime logs."""
