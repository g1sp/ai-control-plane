"""Tests for alert delivery queue."""

import pytest
import asyncio
from datetime import datetime, timedelta
from backend.src.services.alert_delivery_queue import (
    AlertDeliveryQueue,
    QueueItem,
    QueueItemStatus,
)


class TestQueueItem:
    """Test queue item model."""

    def test_create_queue_item(self):
        """Test creating queue item."""
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="high_cost_query",
            alert_title="High Cost Query",
            alert_message="Query exceeded threshold",
            alert_level="warning",
            trigger_value=15.0,
            threshold=10.0,
        )

        assert item.id == "item-1"
        assert item.status == QueueItemStatus.PENDING
        assert item.retry_count == 0

    def test_should_retry(self):
        """Test retry determination."""
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
            status=QueueItemStatus.FAILED,
            retry_count=1,
        )

        assert item.should_retry() is True

        item.retry_count = 3  # Max retries
        assert item.should_retry() is False

    def test_calculate_next_retry(self):
        """Test next retry time calculation."""
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        # First retry: 1 minute
        item.retry_count = 0
        next_time = item.calculate_next_retry()
        delay = (next_time - datetime.utcnow()).total_seconds()
        assert 55 < delay < 65  # ~60 seconds

        # Second retry: 5 minutes
        item.retry_count = 1
        next_time = item.calculate_next_retry()
        delay = (next_time - datetime.utcnow()).total_seconds()
        assert 295 < delay < 305  # ~300 seconds

    def test_to_dict(self):
        """Test converting to dictionary."""
        now = datetime.utcnow()
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
            created_at=now,
        )

        data = item.to_dict()

        assert data["id"] == "item-1"
        assert data["status"] == "pending"
        assert data["retry_count"] == 0


class TestAlertDeliveryQueue:
    """Test alert delivery queue."""

    @pytest.fixture
    def queue(self):
        """Create queue for testing."""
        return AlertDeliveryQueue()

    @pytest.mark.asyncio
    async def test_initialize(self, queue):
        """Test queue initialization."""
        assert queue.is_running is False
        assert queue.queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, queue):
        """Test starting and stopping queue."""
        await queue.start()
        assert queue.is_running is True
        assert len(queue.worker_tasks) == 3

        await queue.stop()
        assert queue.is_running is False

    @pytest.mark.asyncio
    async def test_enqueue_item(self, queue):
        """Test enqueueing item."""
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        result = await queue.enqueue(item)

        assert result is True
        assert queue.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_process_item_without_router(self, queue):
        """Test processing without router."""
        await queue.start()

        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        await queue.enqueue(item)

        # Wait for processing
        await asyncio.sleep(0.5)

        assert queue.queue.qsize() == 0
        assert len(queue.history) > 0
        assert queue.history[-1].status == QueueItemStatus.SENT

        await queue.stop()

    @pytest.mark.asyncio
    async def test_queue_status(self, queue):
        """Test getting queue status."""
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        await queue.enqueue(item)

        status = queue.get_queue_status()

        assert status["queue_size"] == 1
        assert status["processing_count"] == 0
        assert status["is_running"] is False

    def test_get_history(self, queue):
        """Test retrieving history."""
        items = [
            QueueItem(
                id=f"item-{i}",
                alert_id=f"alert-{i}",
                trigger_type="test",
                alert_title="Test",
                alert_message="Test",
                alert_level="info",
                trigger_value=0,
                threshold=0,
                status=QueueItemStatus.SENT if i % 2 == 0 else QueueItemStatus.FAILED,
            )
            for i in range(10)
        ]

        for item in items:
            queue._record_history(item)

        history = queue.get_history()

        assert len(history) == 10

    def test_get_history_filtered(self, queue):
        """Test filtering history."""
        items = [
            QueueItem(
                id=f"item-{i}",
                alert_id=f"alert-{i}",
                trigger_type="test",
                alert_title="Test",
                alert_message="Test",
                alert_level="info",
                trigger_value=0,
                threshold=0,
                status=QueueItemStatus.SENT if i % 2 == 0 else QueueItemStatus.FAILED,
            )
            for i in range(10)
        ]

        for item in items:
            queue._record_history(item)

        sent_history = queue.get_history(status="sent")

        assert len(sent_history) == 5
        assert all(item["status"] == "sent" for item in sent_history)

    def test_history_limit(self, queue):
        """Test history respects size limit."""
        for i in range(1100):
            item = QueueItem(
                id=f"item-{i}",
                alert_id=f"alert-{i}",
                trigger_type="test",
                alert_title="Test",
                alert_message="Test",
                alert_level="info",
                trigger_value=0,
                threshold=0,
            )
            queue._record_history(item)

        assert len(queue.history) == 1000

    @pytest.mark.asyncio
    async def test_drain_empty_queue(self, queue):
        """Test draining empty queue."""
        result = await queue.drain(timeout=1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_drain_timeout(self, queue):
        """Test drain timeout."""
        # Add item that will never complete
        item = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        queue.processing[item.id] = item

        result = await queue.drain(timeout=0.1)
        assert result is False

    @pytest.mark.asyncio
    async def test_multiple_workers(self, queue):
        """Test multiple workers processing concurrently."""
        await queue.start()

        items = [
            QueueItem(
                id=f"item-{i}",
                alert_id=f"alert-{i}",
                trigger_type="test",
                alert_title="Test",
                alert_message="Test",
                alert_level="info",
                trigger_value=0,
                threshold=0,
            )
            for i in range(10)
        ]

        for item in items:
            await queue.enqueue(item)

        # Wait for processing
        await queue.drain(timeout=5.0)

        assert queue.queue.qsize() == 0
        assert len(queue.history) >= 10

        await queue.stop()

    @pytest.mark.asyncio
    async def test_queue_full(self, queue):
        """Test enqueueing when queue is full."""
        queue = AlertDeliveryQueue(max_queue_size=2)

        item1 = QueueItem(
            id="item-1",
            alert_id="alert-1",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        item2 = QueueItem(
            id="item-2",
            alert_id="alert-2",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        item3 = QueueItem(
            id="item-3",
            alert_id="alert-3",
            trigger_type="test",
            alert_title="Test",
            alert_message="Test",
            alert_level="info",
            trigger_value=0,
            threshold=0,
        )

        await queue.enqueue(item1)
        await queue.enqueue(item2)

        result = await queue.enqueue(item3)

        assert result is False  # Queue full

    @pytest.mark.asyncio
    async def test_get_queue_status_counts(self, queue):
        """Test queue status counters."""
        items = [
            QueueItem(
                id=f"item-{i}",
                alert_id=f"alert-{i}",
                trigger_type="test",
                alert_title="Test",
                alert_message="Test",
                alert_level="info",
                trigger_value=0,
                threshold=0,
                status=QueueItemStatus.SENT if i < 5 else QueueItemStatus.FAILED,
            )
            for i in range(10)
        ]

        for item in items:
            queue._record_history(item)

        status = queue.get_queue_status()

        assert status["total_sent"] == 5
        assert status["total_failed"] == 5
        assert status["history_size"] == 10
