"""Screenshot tool for macOS."""

import asyncio
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from nanobot.agent.tools.base import Tool


class ScreenshotTool(Tool):
    """Tool to capture screenshots on macOS."""
    
    def __init__(
        self,
        workspace: Path,
        enabled: bool = False,
        default_save_dir: str | None = None,
        send_callback: Callable | None = None,
    ):
        self.workspace = workspace
        self.enabled = enabled
        self.send_callback = send_callback
        
        # Set default save directory
        if default_save_dir:
            self.default_save_dir = Path(default_save_dir).expanduser()
        else:
            self.default_save_dir = workspace / "tmp" / "screenshots"
        
        # Create default directory if it doesn't exist
        self.default_save_dir.mkdir(parents=True, exist_ok=True)
        
        # Context for sending messages
        self._channel: str | None = None
        self._chat_id: str | None = None
        self._message_id: str | None = None
    
    def set_context(self, channel: str, chat_id: str, message_id: str | None = None) -> None:
        """Set context for sending messages back to the user."""
        self._channel = channel
        self._chat_id = chat_id
        self._message_id = message_id
    
    @property
    def name(self) -> str:
        return "screenshot"
    
    @property
    def description(self) -> str:
        return "Capture a screenshot on macOS. Supports full screen, window, or area selection."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Capture mode: 'full' for full screen, 'window' for window selection, 'area' for area selection",
                    "enum": ["full", "window", "area"],
                },
                "save_dir": {
                    "type": "string",
                    "description": "Optional directory to save the screenshot. Defaults to workspace/tmp/screenshots",
                },
                "send": {
                    "type": "boolean",
                    "description": "If true, send the screenshot back to the user via message tool",
                    "default": False,
                },
            },
            "required": ["mode"],
        }
    
    async def execute(
        self,
        mode: str,
        save_dir: str | None = None,
        send: bool = False,
        **kwargs: Any,
    ) -> str:
        """Execute screenshot capture."""
        
        # Check if tool is enabled
        if not self.enabled:
            return "Error: Screenshot tool is disabled. Enable it in config with tools.screenshot.enabled = true"
        
        # Check if running on macOS
        if platform.system() != "Darwin":
            return "Error: Screenshot tool is only available on macOS."
        
        # Validate mode
        if mode not in ["full", "window", "area"]:
            return f"Error: Invalid mode '{mode}'. Must be one of: full, window, area"
        
        # Determine save directory
        if save_dir:
            save_path = Path(save_dir).expanduser()
        else:
            save_path = self.default_save_dir
        
        # Create directory if it doesn't exist
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = save_path / filename
        
        # Build screencapture command
        cmd = ["screencapture"]
        
        if mode == "window":
            cmd.append("-w")  # window mode
        elif mode == "area":
            cmd.append("-s")  # selection mode
        # full screen mode uses no additional flags
        
        cmd.append(str(filepath))
        
        try:
            # Check screen recording permission
            permission_check = await self._check_screen_recording_permission()
            if not permission_check["has_permission"]:
                return f"Error: Screen Recording permission is required.\n\n{permission_check['instructions']}"
            
            # Execute screencapture command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                stderr_text = stderr.decode("utf-8", errors="replace").strip()
                if "cannot run" in stderr_text.lower() or "permission" in stderr_text.lower():
                    return f"Error: Failed to capture screenshot. Screen Recording permission may be missing.\n\n{permission_check['instructions']}"
                return f"Error: Failed to capture screenshot. Exit code: {process.returncode}, stderr: {stderr_text}"
            
            # Check if file was created
            if not filepath.exists():
                return "Error: Screenshot file was not created. The capture may have been cancelled."
            
            result = f"Screenshot captured successfully: {filepath}"
            
            # Send via message tool if requested
            if send:
                if self.send_callback and self._channel and self._chat_id:
                    try:
                        # Send the image using the callback
                        from nanobot.bus.events import OutboundMessage
                        
                        # Create message with media attachment
                        await self.send_callback(OutboundMessage(
                            channel=self._channel,
                            chat_id=self._chat_id,
                            content=f"Screenshot captured ({mode} mode)",
                            media=[str(filepath)],
                        ))
                        result += f"\nScreenshot sent to {self._channel}:{self._chat_id}"
                    except Exception as e:
                        result += f"\nFailed to send screenshot: {str(e)}. File saved at: {filepath}"
                else:
                    result += f"\nCannot send screenshot: missing context or callback. File saved at: {filepath}"
            
            return result
            
        except FileNotFoundError:
            return "Error: 'screencapture' command not found. This tool requires macOS."
        except Exception as e:
            return f"Error: Failed to capture screenshot: {str(e)}"
    
    async def _check_screen_recording_permission(self) -> dict[str, Any]:
        """Check if Screen Recording permission is granted on macOS."""
        
        # Try to capture a small test screenshot to check permissions
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Try to capture a 1x1 pixel screenshot (should fail if no permission)
            cmd = ["screencapture", "-x", tmp_path]  # -x: no sound
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            stderr_text = stderr.decode("utf-8", errors="replace").lower()
            
            if process.returncode == 0:
                return {
                    "has_permission": True,
                    "instructions": "",
                }
            else:
                instructions = (
                    "To fix this:\n"
                    "1. Open System Settings > Privacy & Security > Screen Recording\n"
                    "2. Click the lock icon to make changes\n"
                    "3. Find your terminal app (Terminal, iTerm, etc.) in the list\n"
                    "4. Check the box to grant Screen Recording permission\n"
                    "5. Restart your terminal app and try again\n\n"
                    "If the terminal app isn't in the list, you may need to:\n"
                    "1. Quit the terminal app completely\n"
                    "2. Open System Settings > Privacy & Security > Screen Recording\n"
                    "3. Click the '+' button and add your terminal app\n"
                    "4. Check the box to grant permission\n"
                    "5. Restart the terminal app"
                )
                
                return {
                    "has_permission": False,
                    "instructions": instructions,
                }
                
        except Exception:
            # If we can't check, assume permission might be needed
            instructions = (
                "Unable to check Screen Recording permission. Please ensure:\n"
                "1. Open System Settings > Privacy & Security > Screen Recording\n"
                "2. Grant permission to your terminal app\n"
                "3. Restart the terminal app if needed"
            )
            
            return {
                "has_permission": False,  # Assume no permission to be safe
                "instructions": instructions,
            }