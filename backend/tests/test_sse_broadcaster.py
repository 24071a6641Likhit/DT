"""
Tests for the SSE Broadcaster service.
"""
import pytest
import asyncio
from datetime import datetime

from app.services.sse_broadcaster import SSEBroadcaster


@pytest.mark.asyncio
async def test_broadcaster_add_remove_client():
    """Test adding and removing SSE clients."""
    broadcaster = SSEBroadcaster()
    
    # Add client
    queue = broadcaster.add_client()
    assert broadcaster.get_client_count() == 1
    
    # Remove client
    broadcaster.remove_client(queue)
    assert broadcaster.get_client_count() == 0


@pytest.mark.asyncio
async def test_broadcaster_broadcast_to_clients():
    """Test broadcasting messages to clients."""
    broadcaster = SSEBroadcaster()
    
    # Add client
    queue = broadcaster.add_client()
    
    # Broadcast message
    test_data = {'power': 1500.0, 'timestamp': datetime.now()}
    await broadcaster.broadcast('readings', test_data)
    
    # Verify client received message
    message = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert 'event: readings' in message
    assert 'data:' in message
    assert '1500.0' in message
    
    broadcaster.remove_client(queue)


@pytest.mark.asyncio
async def test_broadcaster_multiple_clients():
    """Test broadcasting to multiple clients."""
    broadcaster = SSEBroadcaster()
    
    # Add multiple clients
    queue1 = broadcaster.add_client()
    queue2 = broadcaster.add_client()
    assert broadcaster.get_client_count() == 2
    
    # Broadcast
    await broadcaster.broadcast('test', {'value': 123})
    
    # Both clients should receive
    msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
    
    assert msg1 == msg2
    assert '123' in msg1
    
    broadcaster.remove_client(queue1)
    broadcaster.remove_client(queue2)


@pytest.mark.asyncio
async def test_broadcaster_format_sse_message():
    """Test SSE message formatting."""
    broadcaster = SSEBroadcaster()
    
    message = broadcaster._format_sse_message('test', {'key': 'value'})
    
    assert message.startswith('event: test\n')
    assert 'data: ' in message
    assert message.endswith('\n\n')
    assert 'value' in message


@pytest.mark.asyncio
async def test_broadcaster_queue_full_handling():
    """Test handling of full client queues."""
    broadcaster = SSEBroadcaster()
    
    # Add client
    queue = broadcaster.add_client()
    
    # Fill the queue beyond capacity (maxsize=10)
    for i in range(15):
        await broadcaster.broadcast('test', {'index': i})
        
    # Should not raise error, just drop messages
    assert broadcaster.get_client_count() == 1
    
    broadcaster.remove_client(queue)
