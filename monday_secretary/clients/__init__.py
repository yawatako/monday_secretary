"""Client package for Monday Secretary."""

from .base import BaseClient, DEFAULT_RETRY
from .health   import HealthClient
from .calendar import CalendarClient
from .memory   import MemoryClient
from .work     import WorkClient
from .tasks    import TasksClient

__all__ = [
    "BaseClient",
    "HealthClient",
    "CalendarClient",
    "MemoryClient",
    "WorkClient",
    "TasksClient",
]
