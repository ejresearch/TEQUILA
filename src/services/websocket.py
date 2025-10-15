"""WebSocket manager for real-time progress updates during curriculum generation."""
from typing import Dict, List
from fastapi import WebSocket
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time progress updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.generation_status: Dict[int, Dict] = {}  # week_number -> status

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def update_progress(self, week: int, day: int, field: int, total_fields: int,
                             status: str, message: str, attempt: int = 1, max_attempts: int = 10):
        """
        Update and broadcast generation progress.

        Args:
            week: Week number
            day: Day number (1-4)
            field: Current field number
            total_fields: Total fields to generate
            status: Status (generating, validating, completed, error)
            message: Status message
            attempt: Current retry attempt
            max_attempts: Maximum retry attempts
        """
        progress = {
            "type": "progress",
            "week": week,
            "day": day,
            "field": field,
            "totalFields": total_fields,
            "status": status,
            "message": message,
            "attempt": attempt,
            "maxAttempts": max_attempts,
            "percentage": round((field / total_fields) * 100, 1)
        }

        self.generation_status[week] = progress
        await self.broadcast(progress)

    async def update_validation(self, week: int, is_valid: bool, summary: str,
                               error_count: int = 0, warning_count: int = 0):
        """
        Update and broadcast validation results.

        Args:
            week: Week number
            is_valid: Whether validation passed
            summary: Validation summary
            error_count: Number of errors
            warning_count: Number of warnings
        """
        validation = {
            "type": "validation",
            "week": week,
            "isValid": is_valid,
            "summary": summary,
            "errorCount": error_count,
            "warningCount": warning_count
        }

        await self.broadcast(validation)

    async def send_error(self, week: int, error: str):
        """
        Send error notification.

        Args:
            week: Week number
            error: Error message
        """
        error_msg = {
            "type": "error",
            "week": week,
            "message": error
        }

        await self.broadcast(error_msg)

    def get_status(self, week: int) -> Dict:
        """Get current generation status for a week."""
        return self.generation_status.get(week, {})


# Global connection manager instance
manager = ConnectionManager()
