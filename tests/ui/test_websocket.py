"""
Tests for WebSocket connection manager and endpoint.

Tests cover connection management, broadcasting, and disconnect handling.
"""

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from app.main import app
from app.ui.websocket import ConnectionManager, manager


class TestConnectionManager:
    """Test cases for ConnectionManager class."""

    @pytest.fixture
    def connection_manager(self):
        """Create a fresh ConnectionManager instance for testing."""
        return ConnectionManager()

    def test_init(self, connection_manager):
        """Test ConnectionManager initialization."""
        assert connection_manager.active_connections == set()
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_connect(self, connection_manager, mocker):
        """Test WebSocket connection."""
        # Mock WebSocket
        mock_websocket = mocker.Mock(spec=WebSocket)
        mock_websocket.accept = mocker.AsyncMock()

        # Connect
        await connection_manager.connect(mock_websocket)

        # Verify
        mock_websocket.accept.assert_awaited_once()
        assert mock_websocket in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1

    def test_disconnect(self, connection_manager, mocker):
        """Test WebSocket disconnection."""
        # Mock WebSocket
        mock_websocket = mocker.Mock(spec=WebSocket)

        # Add to connections manually
        connection_manager.active_connections.add(mock_websocket)
        assert len(connection_manager.active_connections) == 1

        # Disconnect
        connection_manager.disconnect(mock_websocket)

        # Verify
        assert mock_websocket not in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_single_client(self, connection_manager, mocker):
        """Test broadcasting message to a single connected client."""
        # Mock WebSocket
        mock_websocket = mocker.Mock(spec=WebSocket)
        mock_websocket.send_json = mocker.AsyncMock()

        # Add connection
        connection_manager.active_connections.add(mock_websocket)

        # Broadcast message
        message = {"type": "job_update", "job_id": "test-123", "status": "completed"}
        await connection_manager.broadcast(message)

        # Verify
        mock_websocket.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self, connection_manager, mocker):
        """Test broadcasting message to multiple connected clients."""
        # Mock multiple WebSockets
        mock_ws1 = mocker.Mock(spec=WebSocket)
        mock_ws1.send_json = mocker.AsyncMock()
        mock_ws2 = mocker.Mock(spec=WebSocket)
        mock_ws2.send_json = mocker.AsyncMock()

        # Add connections
        connection_manager.active_connections.add(mock_ws1)
        connection_manager.active_connections.add(mock_ws2)

        # Broadcast message
        message = {"type": "pipeline_update", "data": {"active": 5}}
        await connection_manager.broadcast(message)

        # Verify both received message
        mock_ws1.send_json.assert_awaited_once_with(message)
        mock_ws2.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self, connection_manager, caplog):
        """Test broadcasting when no clients are connected."""
        # Broadcast with no connections
        message = {"type": "test", "data": {}}
        await connection_manager.broadcast(message)

        # Should not raise error, just log
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_client(self, connection_manager, mocker):
        """Test that failed client is removed during broadcast."""
        # Mock WebSockets - one working, one failing
        mock_ws_ok = mocker.Mock(spec=WebSocket)
        mock_ws_ok.send_json = mocker.AsyncMock()

        mock_ws_fail = mocker.Mock(spec=WebSocket)
        mock_ws_fail.send_json = mocker.AsyncMock(side_effect=Exception("Connection lost"))

        # Add connections
        connection_manager.active_connections.add(mock_ws_ok)
        connection_manager.active_connections.add(mock_ws_fail)
        assert len(connection_manager.active_connections) == 2

        # Broadcast message
        message = {"type": "test"}
        await connection_manager.broadcast(message)

        # Verify failed client was removed
        assert mock_ws_ok in connection_manager.active_connections
        assert mock_ws_fail not in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1


class TestWebSocketEndpoint:
    """Test cases for WebSocket FastAPI endpoint."""

    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is registered."""
        # Check endpoint is in routes
        websocket_routes = [route for route in app.routes if hasattr(route, "path") and route.path == "/ws/status"]
        assert len(websocket_routes) == 1

    def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        client = TestClient(app)

        with client.websocket_connect("/ws/status") as websocket:
            # Connection should be established
            assert websocket is not None

            # Test sending message from server (if needed)
            # This tests the connection is open and working


def test_singleton_manager():
    """Test that manager is a singleton instance."""

    assert isinstance(manager, ConnectionManager)
    assert manager.active_connections == set()
