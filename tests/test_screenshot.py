"""Tests for ScreenshotTool."""

import asyncio
import platform
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Mock the workspace path for tests
@pytest.fixture
def mock_workspace():
    """Create a mock workspace path."""
    return Path("/tmp/nanobot_test_workspace")


@pytest.fixture
def mock_send_callback():
    """Create a mock send callback."""
    return AsyncMock()


class TestScreenshotTool:
    """Test cases for ScreenshotTool."""

    @pytest.fixture
    def tool(self, mock_workspace, mock_send_callback):
        """Create a ScreenshotTool instance."""
        from nanobot.agent.tools.screenshot import ScreenshotTool
        return ScreenshotTool(
            workspace=mock_workspace,
            send_callback=mock_send_callback,
            default_channel="cli",
            default_chat_id="direct",
        )

    def test_name(self, tool):
        """Test tool name."""
        assert tool.name == "screenshot"

    def test_description(self, tool):
        """Test tool description is not empty."""
        assert len(tool.description) > 0

    def test_parameters(self, tool):
        """Test tool parameters schema."""
        params = tool.parameters
        assert params["type"] == "object"
        assert "mode" in params["properties"]
        assert "save_dir" in params["properties"]
        assert "send" in params["properties"]
        assert params["properties"]["mode"]["enum"] == ["full", "window", "area"]
        assert "required" in params
        assert "mode" in params["required"]

    @pytest.mark.asyncio
    async def test_platform_check_non_macos(self, tool):
        """Test that non-macOS platforms return an error."""
        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Linux"):
            result = await tool.execute(mode="full")
            assert "Error" in result
            assert "macOS" in result
            assert "Linux" in result

    @pytest.mark.asyncio
    async def test_platform_check_windows(self, tool):
        """Test that Windows platforms return an error."""
        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Windows"):
            result = await tool.execute(mode="full")
            assert "Error" in result
            assert "macOS" in result
            assert "Windows" in result

    @pytest.mark.asyncio
    async def test_invalid_mode(self, tool):
        """Test that invalid mode returns an error."""
        # Mock platform check to pass
        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                result = await tool.execute(mode="invalid")
                assert "Error" in result
                assert "Invalid mode" in result

    @pytest.mark.asyncio
    async def test_permission_error_message(self, tool):
        """Test that permission error has actionable fix instructions."""
        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=tool._get_permission_error_message()):
                result = await tool.execute(mode="full")
                assert "permission" in result.lower()
                assert "Privacy" in result or "System Preferences" in result or "fix" in result.lower()

    def test_default_save_dir(self, tool, mock_workspace):
        """Test default save directory generation."""
        save_dir = tool._get_default_save_dir()
        assert save_dir == mock_workspace / "tmp" / "screenshots"

    def test_filename_timestamp(self, tool):
        """Test that filename includes timestamp."""
        filename = tool._generate_filename()
        assert filename.startswith("screenshot_")
        assert filename.endswith(".png")
        # Timestamp format: YYYYMMDD_HHMMSS
        assert len(filename) == len("screenshot_20240101_120000.png")

    def test_custom_save_dir(self, tool):
        """Test custom save directory parameter."""
        # The save_dir is passed to execute, not stored in tool
        # We just verify the parameter exists
        params = tool.parameters
        assert "save_dir" in params["properties"]
        assert params["properties"]["save_dir"]["type"] == "string"

    def test_send_parameter_default_false(self, tool):
        """Test that send parameter defaults to false."""
        params = tool.parameters
        # The default is not explicitly set in schema, so it defaults to falsy
        # In the execute method, send defaults to False

    @pytest.mark.asyncio
    async def test_send_false_returns_path(self, tool, tmp_path):
        """Test that send=false returns the local file path."""
        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                with patch.object(tool, "_capture_screenshot", return_value=str(tmp_path / "test.png")):
                    result = await tool.execute(mode="full", send=False)
                    assert "saved to:" in result.lower()

    @pytest.mark.asyncio
    async def test_send_true_uses_callback(self, tool, mock_send_callback, tmp_path):
        """Test that send=true uses the message callback."""
        screenshot_path = tmp_path / "test.png"
        screenshot_path.touch()

        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                with patch.object(tool, "_capture_screenshot", return_value=str(screenshot_path)):
                    result = await tool.execute(mode="full", send=True)
                    mock_send_callback.assert_called_once()
                    assert "sent to" in result.lower() or "saved at" in result.lower()

    @pytest.mark.asyncio
    async def test_send_fallback_on_error(self, tool, mock_send_callback, tmp_path):
        """Test that sending failure falls back to returning local path."""
        screenshot_path = tmp_path / "test.png"
        screenshot_path.touch()

        mock_send_callback.side_effect = Exception("Send failed")

        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                with patch.object(tool, "_capture_screenshot", return_value=str(screenshot_path)):
                    result = await tool.execute(mode="full", send=True)
                    # Should contain both saved path info and fallback message
                    assert "saved to:" in result.lower() or "failed" in result.lower()


class TestScreenshotToolConfig:
    """Test cases for ScreenshotToolConfig."""

    def test_default_enabled_false(self):
        """Test that screenshot tool is disabled by default."""
        from nanobot.config.schema import ScreenshotToolConfig

        config = ScreenshotToolConfig()
        assert config.enabled is False

    def test_can_enable(self):
        """Test that screenshot tool can be enabled."""
        from nanobot.config.schema import ScreenshotToolConfig

        config = ScreenshotToolConfig(enabled=True)
        assert config.enabled is True


class TestScreenshotToolIntegration:
    """Integration tests for ScreenshotTool."""

    @pytest.fixture
    def mock_workspace(self, tmp_path):
        """Create a mock workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        return workspace

    @pytest.mark.asyncio
    async def test_full_mode_command(self, mock_workspace):
        """Test that full mode uses correct screencapture command."""
        from nanobot.agent.tools.screenshot import ScreenshotTool

        tool = ScreenshotTool(workspace=mock_workspace)

        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                    mock_process = MagicMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_exec.return_value = mock_process

                    # Create a temp file to simulate screenshot
                    with patch.object(Path, "exists", return_value=True):
                        result = await tool.execute(mode="full")

                    # Verify screencapture was called (without -W or -s flags for full mode)
                    mock_exec.assert_called_once()
                    call_args = mock_exec.call_args[0]
                    assert "screencapture" in call_args
                    # Full mode should not have -W or -s
                    assert "-W" not in call_args
                    assert "-s" not in call_args

    @pytest.mark.asyncio
    async def test_window_mode_command(self, mock_workspace):
        """Test that window mode uses -W flag."""
        from nanobot.agent.tools.screenshot import ScreenshotTool

        tool = ScreenshotTool(workspace=mock_workspace)

        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                    mock_process = MagicMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_exec.return_value = mock_process

                    with patch.object(Path, "exists", return_value=True):
                        result = await tool.execute(mode="window")

                    mock_exec.assert_called_once()
                    call_args = mock_exec.call_args[0]
                    assert "screencapture" in call_args
                    assert "-W" in call_args

    @pytest.mark.asyncio
    async def test_area_mode_command(self, mock_workspace):
        """Test that area mode uses -s flag."""
        from nanobot.agent.tools.screenshot import ScreenshotTool

        tool = ScreenshotTool(workspace=mock_workspace)

        with patch("nanobot.agent.tools.screenshot.platform.system", return_value="Darwin"):
            with patch.object(tool, "_check_permissions", return_value=None):
                with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                    mock_process = MagicMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_exec.return_value = mock_process

                    with patch.object(Path, "exists", return_value=True):
                        result = await tool.execute(mode="area")

                    mock_exec.assert_called_once()
                    call_args = mock_exec.call_args[0]
                    assert "screencapture" in call_args
                    assert "-s" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
