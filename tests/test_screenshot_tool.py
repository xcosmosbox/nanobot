"""Tests for screenshot tool."""

import platform
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nanobot.agent.tools.screenshot import ScreenshotTool


class TestScreenshotTool:
    """Test screenshot tool functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.workspace = Path(tempfile.mkdtemp())
        self.tool = ScreenshotTool(
            workspace=self.workspace,
            enabled=True,
        )
    
    def test_tool_properties(self):
        """Test tool name, description, and parameters."""
        assert self.tool.name == "screenshot"
        assert "Capture a screenshot on macOS" in self.tool.description
        
        params = self.tool.parameters
        assert params["type"] == "object"
        assert "mode" in params["properties"]
        assert "save_dir" in params["properties"]
        assert "send" in params["properties"]
        assert params["properties"]["mode"]["enum"] == ["full", "window", "area"]
        assert params["properties"]["send"]["default"] is False
        assert "mode" in params["required"]
    
    def test_tool_disabled(self):
        """Test tool when disabled."""
        tool = ScreenshotTool(workspace=self.workspace, enabled=False)
        assert tool.enabled is False
    
    def test_set_context(self):
        """Test setting context for message sending."""
        self.tool.set_context("telegram", "12345", "msg_123")
        assert self.tool._channel == "telegram"
        assert self.tool._chat_id == "12345"
        assert self.tool._message_id == "msg_123"
    
    @pytest.mark.skipif(platform.system() == "Darwin", reason="Test on non-macOS")
    @pytest.mark.asyncio
    async def test_non_macos_error(self):
        """Test error on non-macOS systems."""
        # Mock platform.system to return non-Darwin
        with patch('platform.system', return_value='Linux'):
            tool = ScreenshotTool(workspace=self.workspace, enabled=True)
            result = await tool.execute(mode="full")
            assert "Error: Screenshot tool is only available on macOS" in result
    
    @pytest.mark.asyncio
    async def test_invalid_mode(self):
        """Test error for invalid mode."""
        # Mock platform.system to return Darwin (macOS)
        with patch('platform.system', return_value='Darwin'):
            result = await self.tool.execute(mode="invalid")
            assert "Error: Invalid mode 'invalid'" in result
    
    def test_validate_params(self):
        """Test parameter validation."""
        # Valid parameters
        errors = self.tool.validate_params({"mode": "full"})
        assert errors == []
        
        errors = self.tool.validate_params({"mode": "full", "send": True})
        assert errors == []
        
        errors = self.tool.validate_params({"mode": "full", "save_dir": "/tmp"})
        assert errors == []
        
        # Invalid mode
        errors = self.tool.validate_params({"mode": "invalid"})
        assert len(errors) > 0
        
        # Missing required mode
        errors = self.tool.validate_params({})
        assert len(errors) > 0
    
    @patch('asyncio.create_subprocess_exec')
    @patch('nanobot.agent.tools.screenshot.ScreenshotTool._check_screen_recording_permission')
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_check_permission, mock_subprocess):
        """Test successful screenshot capture."""
        mock_check_permission.return_value = {
            "has_permission": True,
            "instructions": ""
        }
        
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_subprocess.return_value = mock_process
        
        # Mock file exists check
        with patch('pathlib.Path.exists', return_value=True):
            result = await self.tool.execute(mode="full")
            assert "Screenshot captured successfully" in result
    
    @patch('asyncio.create_subprocess_exec')
    @patch('nanobot.agent.tools.screenshot.ScreenshotTool._check_screen_recording_permission')
    @pytest.mark.asyncio
    async def test_execute_no_permission(self, mock_check_permission, mock_subprocess):
        """Test screenshot capture without permission."""
        mock_check_permission.return_value = {
            "has_permission": False,
            "instructions": "Fix instructions"
        }
        
        result = await self.tool.execute(mode="full")
        assert "Error: Screen Recording permission is required" in result
        assert "Fix instructions" in result
    
    @patch('asyncio.create_subprocess_exec')
    @patch('nanobot.agent.tools.screenshot.ScreenshotTool._check_screen_recording_permission')
    @pytest.mark.asyncio
    async def test_execute_command_failed(self, mock_check_permission, mock_subprocess):
        """Test screenshot capture when command fails."""
        mock_check_permission.return_value = {
            "has_permission": True,
            "instructions": ""
        }
        
        # Mock subprocess failure
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"Command failed")
        mock_subprocess.return_value = mock_process
        
        result = await self.tool.execute(mode="full")
        assert "Error: Failed to capture screenshot" in result
    
    @patch('asyncio.create_subprocess_exec')
    @patch('nanobot.agent.tools.screenshot.ScreenshotTool._check_screen_recording_permission')
    @pytest.mark.asyncio
    async def test_execute_file_not_created(self, mock_check_permission, mock_subprocess):
        """Test screenshot capture when file is not created."""
        mock_check_permission.return_value = {
            "has_permission": True,
            "instructions": ""
        }
        
        # Mock subprocess success but file doesn't exist
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_subprocess.return_value = mock_process
        
        # Mock file exists check to return False
        with patch('pathlib.Path.exists', return_value=False):
            result = await self.tool.execute(mode="full")
            assert "Error: Screenshot file was not created" in result
    
    @patch('asyncio.create_subprocess_exec')
    @patch('nanobot.agent.tools.screenshot.ScreenshotTool._check_screen_recording_permission')
    async def test_execute_with_send(self, mock_check_permission, mock_subprocess):
        """Test screenshot capture with send=True."""
        mock_check_permission.return_value = {
            "has_permission": True,
            "instructions": ""
        }
        
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_subprocess.return_value = mock_process
        
        # Mock file exists check
        with patch('pathlib.Path.exists', return_value=True):
            # Test without context (should fail to send)
            result = await self.tool.execute(mode="full", send=True)
            assert "Screenshot captured successfully" in result
            assert "Cannot send screenshot: missing context or callback" in result
            
            # Test with context but no callback
            self.tool.set_context("telegram", "12345")
            result = await self.tool.execute(mode="full", send=True)
            assert "Cannot send screenshot: missing context or callback" in result
    
    @patch('asyncio.create_subprocess_exec')
    @patch('nanobot.agent.tools.screenshot.ScreenshotTool._check_screen_recording_permission')
    async def test_execute_with_send_and_callback(self, mock_check_permission, mock_subprocess):
        """Test screenshot capture with send=True and callback."""
        mock_check_permission.return_value = {
            "has_permission": True,
            "instructions": ""
        }
        
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_subprocess.return_value = mock_process
        
        # Mock callback
        mock_callback = AsyncMock()
        tool = ScreenshotTool(
            workspace=self.workspace,
            enabled=True,
            send_callback=mock_callback,
        )
        tool.set_context("telegram", "12345")
        
        # Mock file exists check
        with patch('pathlib.Path.exists', return_value=True):
            result = await tool.execute(mode="full", send=True)
            assert "Screenshot captured successfully" in result
            assert "Screenshot sent to telegram:12345" in result
            mock_callback.assert_called_once()
    
    def test_custom_save_dir(self):
        """Test with custom save directory."""
        custom_dir = Path(tempfile.mkdtemp())
        tool = ScreenshotTool(
            workspace=self.workspace,
            enabled=True,
            default_save_dir=str(custom_dir),
        )
        
        # Check that custom directory is used
        assert tool.default_save_dir == custom_dir
        
        # Check that directory was created
        assert custom_dir.exists()