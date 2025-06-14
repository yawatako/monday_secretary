"""Client package for Monday Secretary."""

from .health   import HealthClient
from .calendar import CalendarClient
from .memory   import MemoryClient
from .work     import WorkClient

__all__ = [
    "HealthClient",
    "CalendarClient",
    "MemoryClient",
    "WorkClient",
]
