from dataclasses import dataclass


@dataclass
class CPU:
    """
    Model for holding information about a CPU.
    """
    id: str
    minimum_frequency: float
    maximum_frequency: float
    current_frequency: float
    utilization: float
