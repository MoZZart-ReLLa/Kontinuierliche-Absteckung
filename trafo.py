from dataclasses import dataclass


@dataclass
class Point:
    X: float
    Y: float
    Z: float


def position_image(P1: Point, P2: Point):
