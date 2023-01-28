from dataclasses import dataclass


@dataclass
class CPU:
    """
    Model for holding information about a CPU with frequencies in MHz and utilization in %
    """
    id: str
    physical_id: str
    minimum_frequency: float
    maximum_frequency: float
    current_frequency: float
    temperature: float
    utilization: float
