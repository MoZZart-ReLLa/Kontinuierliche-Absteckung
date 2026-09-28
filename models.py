from dataclasses import dataclass
from typing import Optional
from enum import Enum
from math import sqrt


### DATACLASS ###

@dataclass
class Point:
    X: float
    Y: float
    Z: float
    number: Optional[int] = None

    def distance(self, other: Point):
        
        return sqrt( (self.X-other.X)**2 + (self.Y-other.Y)**2 + (self.Z-other.Z)**2 )

    def nearest(self, points: List[Point]):

        if not points:
            return None, None

        idx, nearest = min(enumerate(points), key=lambda item: self.distance(item[1]))
        return idx, nearest




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
