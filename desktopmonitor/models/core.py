from dataclasses import dataclass
from typing import Dict

from .cpu import CPU


@dataclass
class Core:
    """
    Model for holding information about a CPU Core.
    """
    id: str
    cpus_by_id: Dict[str, CPU]
