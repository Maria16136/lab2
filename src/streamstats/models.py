from dataclasses import dataclass


@dataclass
class Event:
    timestamp: str
    level: str
    source: str
    message: str