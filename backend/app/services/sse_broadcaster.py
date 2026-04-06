"""
Server-Sent Events (SSE) broadcaster for real-time updates.
Manages connected clients and broadcasts readings.
"""
import asyncio
import json
from typing import Set, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    """Manages SSE connections and broadcasts updates to all clients."""
    
    def __init__(self):
        self._clients: Set[asyncio.Queue] = set()
        self._running = False
        
    def add_client(self) -> asyncio.Queue:
        """Add a new SSE client connection."""
        queue = asyncio.Queue(maxsize=10)  # Buffer up to 10 messages
        self._clients.add(queue)
        logger.info(f"SSE client connected. Total clients: {len(self._clients)}")
        return queue
        
    def remove_client(self, queue: asyncio.Queue):
        """Remove a disconnected SSE client."""
        self._clients.discard(queue)
        logger.info(f"SSE client disconnected. Total clients: {len(self._clients)}")
        
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event (e.g., 'readings', 'alert', 'device_update')
            data: Event payload as dictionary
        """
        if not self._clients:
            return
            
        message = self._format_sse_message(event_type, data)
        
        # Send to all clients, removing disconnected ones
        disconnected = set()
        
        for queue in self._clients:
            try:
                # Non-blocking put, skip if queue is full
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("Client queue full, dropping message")
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(queue)
                
        # Clean up disconnected clients
        for queue in disconnected:
            self.remove_client(queue)
            
    def _format_sse_message(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as SSE message format."""
        json_data = json.dumps(data, default=str)  # default=str handles datetime
        return f"event: {event_type}\ndata: {json_data}\n\n"
        
    async def broadcast_readings(self, readings: Dict[str, Any]):
        """Broadcast current readings update."""
        await self.broadcast('readings', {
            'timestamp': datetime.now().isoformat(),
            'readings': readings
        })
        
    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast new alert notification."""
        await self.broadcast('alert', alert)
        
    async def broadcast_device_update(self, device: Dict[str, Any]):
        """Broadcast device configuration update."""
        await self.broadcast('device_update', device)
        
    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)


# Global broadcaster instance
broadcaster = SSEBroadcaster()
