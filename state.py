import numpy as np
from models import *



### Global variables ###

# tachy objects
tachy_1 = None
tachy_2 = None

measure_tachy = None
drawing_tacky = None

# prism types
reference_prism_t = PRISMTYPE.PRISM_ROUND
rover_prism_t = PRISMTYPE.PRISM_360_MINI

# prism heights
prism1_height: float = None
prism2_height: float = None
prism3_height: float = None
rover_prism_height: float = None

# Points of reference prisms
P1: Point = None
P2: Point = None
P3: Point = None

s = 1.0
R = np.array([[1,0,0],[0,1,0],[0,0,1]])
t = np.array([[0],[0],[0]])

# state values
drawing = False
index_offset = 2