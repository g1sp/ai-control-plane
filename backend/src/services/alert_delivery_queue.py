"""Asynchronous alert delivery queue with retry logic."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class QueueItemStatus(str, Enum):
    """Status of queued delivery item."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueueItem:
    """Item in the delivery queue."""
    id: str
    alert_id: str
    trigger_type: str
    alert_title: str
    alert_message: str
    alert_level: str
    trigger_value: Any
    threshold: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: QueueItemStatus = QueueItemStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    next_retry_time: Optional[datetime] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None

    def should_retry(self) -> bool:
        """Check if item should be retried."""
        if self.status != QueueItemStatus.FAILED:
            return False
        if self.retry_count >= self.max_retries:
            return False
        if self.next_retry_time is None:
            return True
        return datetime.utcnow() >= self.next_retry_time

    def calculate_next_retry(self) -> datetime:
        """Calculate when to retry based on retry count."""
        # Exponential backoff: 1min, 5min, 15min
        delays = [60, 300, 900]
        delay = delays[min(self.retry_count, len(delays) - 1)]
        return datetime.utcnow() + timedelta(seconds=delay)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "trigger_type": self.trigger_type,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error_message": self.error_message,
        }


class AlertDeliveryQueue:
    """Asynchronous queue for alert deliveries with retry logic."""

    def __init__(self, alert_channel_router=None, max_queue_size: int = 10000):
        """Initialize delivery queue."""
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.alert_channel_router = alert_channel_router
        self.processing: Dict[str, QueueItem] = {}
        self.history: List[QueueItem] = []
        self.max_history = 1000
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.num_workers = 3  # Number of concurrent workers

    async def start(self) -> None:
        """Start the delivery queue processing."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("Starting alert delivery queue")

        # Start worker tasks
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(i))
            self.worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the delivery queue processing."""
        self.is_running = False
        logger.info("Stopping alert delivery queue")

        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

    async def enqueue(self, item: QueueItem) -> bool:
        """Add item to delivery queue."""
        try:
            self.queue.put_nowait(item)
            logger.debug(f"Enqueued alert delivery: {item.id}")
            return True
        except asyncio.QueueFull:
            logger.error(f"Delivery queue full, dropping item: {item.id}")
            return False

    async def _worker(self, worker_id: int) -> None:
        """Worker task that processes deliveries."""
        logger.info(f"Delivery queue worker {worker_id} started")

        while self.is_running:
            try:
                # Get next item from queue with timeout
                item = await asyncio.wait_for(self.queue.get(), timeout=5.0)

                try:
                    await self._process_item(item)
                except Exception as e:
                    logger.error(f"Error processing item {item.id}: {e}", exc_info=True)
                    await self._handle_failure(item, str(e))

            except asyncio.TimeoutError:
                # No items in queue, check for retries
                await self._process_retries()

            except asyncio.CancelledError:
                logger.info(f"Delivery queue worker {worker_id} cancelled")
                break

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

    async def _process_item(self, item: QueueItem) -> None:
        """Process a delivery item."""
        item.status = QueueItemStatus.PROCESSING
        self.processing[item.id] = item

        try:
            # Route alert through channels
            if self.alert_channel_router:
                delivery_records = await self.alert_channel_router.route_alert(
                    alert_id=item.alert_id,
                    trigger_type=item.trigger_type,
                    alert_title=item.alert_title,
                    alert_message=item.alert_message,
                    alert_level=item.alert_level,
                    trigger_value=item.trigger_value,
                    threshold=item.threshold,
                )

                # Check if all deliveries succeeded
                all_successful = all(
                    r.status.value == "sent" for r in delivery_records
                )

                if all_successful:
                    item.status = QueueItemStatus.SENT
                    item.processed_at = datetime.utcnow()
                    logger.info(f"Alert {item.alert_id} delivered successfully")
                else:
                    raise Exception("Some channels failed to deliver")
            else:
                logger.warning("No alert channel router configured")
                item.status = QueueItemStatus.SENT
                item.processed_at = datetime.utcnow()

        except Exception as e:
            await self._handle_failure(item, str(e))

        finally:
            del self.processing[item.id]
            self._record_history(item)

    async def _handle_failure(self, item: QueueItem, error: str) -> None:
        """Handle delivery failure."""
        item.error_message = error
        item.retry_count += 1

        if item.retry_count >= item.max_retries:
            item.status = QueueItemStatus.FAILED
            logger.error(f"Alert {item.alert_id} failed after {item.retry_count} retries: {error}")
        else:
            item.status = QueueItemStatus.RETRYING
            item.next_retry_time = item.calculate_next_retry()
            # Re-enqueue for retry
            await self.enqueue(item)
            logger.warning(
                f"Alert {item.alert_id} will retry in {(item.next_retry_time - datetime.utcnow()).total_seconds():.0f}s"
            )

    async def _process_retries(self) -> None:
        """Check for items that need retry."""
        # Get items from history that need retry
        retry_items = [
            item
            for item in self.history
            if item.status == QueueItemStatus.RETRYING and item.should_retry()
        ]

        for item in retry_items:
            item.status = QueueItemStatus.PENDING
            await self.enqueue(item)
            logger.info(f"Re-enqueued alert {item.alert_id} for retry")

    def _record_history(self, item: QueueItem) -> None:
        """Record item in history."""
        self.history.append(item)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            "queue_size": self.queue.qsize(),
            "processing_count": len(self.processing),
            "history_size": len(self.history),
            "is_running": self.is_running,
            "num_workers": self.num_workers,
            "total_pending": sum(1 for item in self.history if item.status == QueueItemStatus.PENDING),
            "total_sent": sum(1 for item in self.history if item.status == QueueItemStatus.SENT),
            "total_failed": sum(1 for item in self.history if item.status == QueueItemStatus.FAILED),
            "total_retrying": sum(1 for item in self.history if item.status == QueueItemStatus.RETRYING),
        }

    def get_history(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get delivery history."""
        items = self.history

        if status:
            items = [item for item in items if item.status.value == status]

        return [item.to_dict() for item in items[-limit:]]

    async def drain(self, timeout: float = 30.0) -> bool:
        """Wait for queue to be empty."""
        try:
            start_time = datetime.utcnow()
            while self.queue.qsize() > 0 or self.processing:
                if (datetime.utcnow() - start_time).total_seconds() > timeout:
                    logger.warning(f"Queue drain timeout after {timeout}s")
                    return False
                await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Error draining queue: {e}")
            return False


# Global instance
_delivery_queue: Optional[AlertDeliveryQueue] = None


def get_delivery_queue(alert_channel_router=None) -> AlertDeliveryQueue:
    """Get or create global delivery queue."""
    global _delivery_queue
    if _delivery_queue is None:
        _delivery_queue = AlertDeliveryQueue(alert_channel_router)
    return _delivery_queue
