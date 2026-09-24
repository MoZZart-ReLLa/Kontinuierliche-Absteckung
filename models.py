from dataclasses import dataclass
from typing import Optional
from enum import Enum


### DATACLASS ###

@dataclass
class Point:
    X: float
    Y: float
    Z: float
    number: Optional[int] = None



@dataclass
class Line:
    number: int
    points: list[Point]



class PRISMTYPE(Enum):
    PRISM_ROUND = 0  # Leica circular prism
    PRISM_MINI = 1  # Leica mini prism
    PRISM_TAPE = 2  # Leica reflector tape
    PRISM_360 = 3  # Leica 360-degree prism
    PRISM_360_MINI = 7  # Leica mini 360-degree prism
    PRISM_MINI_ZERO = 8  # Leica mini zero prism
    PRISM_USER = 9  # User-defined prism
    PRISM_NDS_TAPE = 10  # Leica HDS target
