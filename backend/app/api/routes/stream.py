"""
SSE (Server-Sent Events) streaming endpoints for real-time updates.
"""
import asyncio
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
import logging

from app.services.sse_broadcaster import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stream", tags=["Stream"])


@router.get("/live")
async def stream_live_updates():
    """
    SSE endpoint for real-time energy monitoring updates.
    
    Clients receive:
    - 'readings' events: Current readings from all devices + unknown load (every 5s)
    - 'alert' events: New alerts as they are created
    - 'device_update' events: Device configuration changes
    
    Example client usage (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/stream/live');
    
    eventSource.addEventListener('readings', (event) => {
        const data = JSON.parse(event.data);
        console.log('Readings:', data.readings);
    });
    
    eventSource.addEventListener('alert', (event) => {
        const alert = JSON.parse(event.data);
        console.log('New alert:', alert);
    });
    
    eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        // Browser automatically reconnects
    };
    ```
    """
    async def event_generator():
        queue = broadcaster.add_client()
        try:
            while True:
                # Wait for next message from broadcaster
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info("SSE client connection cancelled")
        finally:
            broadcaster.remove_client(queue)
            
    return EventSourceResponse(event_generator())


@router.get("/health")
async def stream_health():
    """Get SSE broadcaster health status."""
    return {
        "status": "healthy",
        "connected_clients": broadcaster.get_client_count()
    }
