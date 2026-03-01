"""Screenshot tool for capturing screen on macOS."""

import asyncio
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool


class ScreenshotTool(Tool):
    """Tool to capture screenshots on macOS using screencapture command."""

    def __init__(
        self,
        workspace: Path,
        send_callback: Any = None,
        default_channel: str = "",
        default_chat_id: str = "",
    ):
        self.workspace = workspace
        self._send_callback = send_callback
        self._default_channel = default_channel
        self._default_chat_id = default_chat_id

    def set_context(self, channel: str, chat_id: str) -> None:
        """Set the current message context for sending screenshots."""
        self._default_channel = channel
        self._default_chat_id = chat_id

    def set_send_callback(self, callback: Any) -> None:
        """Set the callback for sending messages."""
        self._send_callback = callback

    @property
    def name(self) -> str:
        return "screenshot"

    @property
    def description(self) -> str:
        return "Capture a screenshot on macOS. Use mode 'full' for full screen, 'window' to select a window, 'area' to select an area."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["full", "window", "area"],
                    "description": "Screenshot mode: 'full' (full screen), 'window' (select window), 'area' (select area)"
                },
                "save_dir": {
                    "type": "string",
                    "description": "Optional: directory to save screenshot (default: workspace/tmp/screenshots)"
                },
                "send": {
                    "type": "boolean",
                    "description": "If true, send the screenshot to the current session (default: false)"
                }
            },
            "required": ["mode"]
        }

    def _get_default_save_dir(self) -> Path:
        """Get the default screenshot save directory."""
        return self.workspace / "tmp" / "screenshots"

    def _generate_filename(self) -> str:
        """Generate a timestamped filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"screenshot_{timestamp}.png"

    def _check_platform(self) -> str | None:
        """Check if running on macOS. Returns error message if not."""
        if platform.system() != "Darwin":
            return ("Error: Screenshot tool is only supported on macOS. "
                    "Your system is running " + platform.system() + ".")
        return None

    async def _check_permissions(self) -> str | None:
        """Check if Screen Recording permission is granted. Returns error with fix instructions if missing."""
        try:
            # Try to capture a small test area to check permissions
            result = await asyncio.create_subprocess_exec(
                "screencapture", "-x", "/tmp/nanobot_screenshot_test.png",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()

            if result.returncode != 0:
                return self._get_permission_error_message()
            return None
        except FileNotFoundError:
            return "Error: screencapture command not found. This tool requires macOS."
        except Exception:
            return self._get_permission_error_message()

    def _get_permission_error_message(self) -> str:
        """Get actionable error message for missing screen recording permission."""
        return (
            "Error: Screen Recording permission is required to capture screenshots.\n\n"
            "To fix this:\n"
            "1. Open System Preferences → Privacy & Security → Screen Recording\n"
            "2. Enable/Allow your terminal application (or the app running nanobot)\n"
            "3. Restart the terminal application after granting permission"
        )

    async def _capture_screenshot(
        self,
        mode: str,
        output_path: Path
    ) -> str:
        """Capture screenshot using macOS screencapture command."""
        # Build the screencapture command based on mode
        cmd = ["screencapture"]

        if mode == "window":
            cmd.append("-W")  # Window mode
        elif mode == "area":
            cmd.append("-s")  # Area selection (mouse drag)
        # mode == "full" doesn't need any special flag

        cmd.append(str(output_path))

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                if "User canceled" in error_msg or result.returncode == 1:
                    return "Error: Screenshot cancelled by user"
                return f"Error capturing screenshot: {error_msg}"

            # Verify the file was created
            if not output_path.exists():
                return "Error: Screenshot file was not created"

            return str(output_path)

        except FileNotFoundError:
            return "Error: screencapture command not found. This tool requires macOS."
        except Exception as e:
            return f"Error capturing screenshot: {str(e)}"

    async def _send_screenshot(self, file_path: str, channel: str, chat_id: str) -> str:
        """Send screenshot to the user via message tool callback."""
        if not self._send_callback:
            return f"Screenshot saved to: {file_path}"

        try:
            from nanobot.bus.events import OutboundMessage
            msg = OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content="Here is your screenshot:",
                media=[file_path],
            )
            await self._send_callback(msg)
            return f"Screenshot sent to {channel}:{chat_id}\nSaved at: {file_path}"
        except Exception as e:
            # Fallback to returning local path if sending fails
            return f"Screenshot saved to: {file_path}\n(Failed to send: {str(e)})"

    async def execute(
        self,
        mode: str,
        save_dir: str | None = None,
        send: bool = False,
        **kwargs: Any
    ) -> str:
        # Check platform
        platform_error = self._check_platform()
        if platform_error:
            return platform_error

        # Check permissions
        perm_error = await self._check_permissions()
        if perm_error:
            return perm_error

        # Validate mode
        valid_modes = ["full", "window", "area"]
        if mode not in valid_modes:
            return f"Error: Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}"

        # Determine save directory
        if save_dir:
            output_dir = Path(save_dir).expanduser().resolve()
        else:
            output_dir = self._get_default_save_dir()

        # Create directory if it doesn't exist
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return f"Error: Could not create directory {output_dir}: {str(e)}"

        # Generate filename
        filename = self._generate_filename()
        output_path = output_dir / filename

        # Capture screenshot
        result = await self._capture_screenshot(mode, output_path)
        if result.startswith("Error"):
            return result

        # Send if requested
        if send:
            channel = self._default_channel or "cli"
            chat_id = self._default_chat_id or "direct"
            return await self._send_screenshot(result, channel, chat_id)

        return f"Screenshot saved to: {result}"
