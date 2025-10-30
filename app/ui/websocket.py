"""
WebSocket connection manager for real-time updates.

This module provides a ConnectionManager class that handles WebSocket connections
and broadcasts messages to all connected clients.
"""

from typing import Set

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.

    This class maintains a set of active WebSocket connections and provides
    methods to connect, disconnect, and broadcast messages to all clients.
    """

    def __init__(self) -> None:
        """Initialize the connection manager with an empty set of connections."""
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a WebSocket connection and add it to active connections.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from active connections.

        Args:
            websocket: The WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected WebSocket clients.

        Args:
            message: Dictionary containing the message to broadcast
                    Expected format: {"type": str, "job_id": str (optional),
                                    "status": str (optional), "data": dict (optional)}
        """
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to")
            return

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.debug(f"Broadcast message type '{message.get('type')}' to client")
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Singleton instance
manager = ConnectionManager()
