import numpy as np
import state
from models import *
import time
from IO import Tachy
import csv
from math import sin, cos
import asyncio


### CSV ###

def open_csv(file_path: str):

    with open(file_path, mode='r', encoding='utf-8') as file:

        reader = csv.reader(file)
        header = next(reader, None)
        
        lines = []
        for row in reader:

            # ignore points with line number 0
            line_number = int(float(row[0])/1000)
            if line_number == 0:
                continue

            # get point
            point = Point(float(row[1]), float(row[2]), float(row[3]), number=int(row[0])%1000)

            # add point to corresponding line
            line = next((l for l in lines if l.number == line_number), None)
            if line:
                line.points.append(point)
            else:
                line = Line(number=line_number, points=[point])
                lines.append(line)

        # sort lines and points by number
        lines.sort(key=lambda l: l.number)
        for line in lines:
            line.points.sort(key=lambda p: p.number)

    return lines



### STATIONING ###

def adjust_station(T1P1, T1P2, T1P3, T2P1, T2P2, T2P3):

    y = np.array([T1P1.X, T1P1.Y, T1P1.Z,
                  T1P2.X, T1P2.Y, T1P2.Z,
                  T1P3.X, T1P3.Y, T1P3.Z,
                  T2P1.X, T2P1.Y, T2P1.Z,
                  T2P2.X, T2P2.Y, T2P2.Z,
                  T2P3.X, T2P3.Y, T2P3.Z]).reshape(-1,1)
    
    x = np.array([T1P1.X, T1P1.Y, T1P1.Z,
                  T1P2.X, T1P2.Y, T1P2.Z,
                  T1P3.X, T1P3.Y, T1P3.Z,
                       0,      0,      0, 0], dtype=float).reshape(-1,1)

    while True:
        x1, y1, z1 = x[0,0], x[1,0], x[2,0]
        x2, y2, z2 = x[3,0], x[4,0], x[5,0]
        x3, y3, z3 = x[6,0], x[7,0], x[8,0]
        tx, ty, tz = x[9,0], x[10,0], x[11,0]
        phi = x[12,0]

        c = cos(phi)
        s = sin(phi)

        f = np.array([x1, y1, z1,
                      x2, y2, z2,
                      x3, y3, z3,
                      c*x1 + s*y1 + tx,
                      -s*x1 + c*y1 + ty,
                      z1 + tz,
                      c*x2 + s*y2 + tx,
                      -s*x2 + c*y2 + ty,
                      z2 + tz,
                      c*x3 + s*y3 + tx,
                      -s*x3 + c*y3 + ty,
                      z3 + tz], dtype=float).reshape(-1,1)

        dy = y - f

        A = np.array([[ 1, 0, 0,  0, 0, 0,  0, 0, 0, 0, 0, 0,          0],
                      [ 0, 1, 0,  0, 0, 0,  0, 0, 0, 0, 0, 0,          0],
                      [ 0, 0, 1,  0, 0, 0,  0, 0, 0, 0, 0, 0,          0],
                      [ 0, 0, 0,  1, 0, 0,  0, 0, 0, 0, 0, 0,          0],
                      [ 0, 0, 0,  0, 1, 0,  0, 0, 0, 0, 0, 0,          0],
                      [ 0, 0, 0,  0, 0, 1,  0, 0, 0, 0, 0, 0,          0],
                      [ 0, 0, 0,  0, 0, 0,  1, 0, 0, 0, 0, 0,          0],
                      [ 0, 0, 0,  0, 0, 0,  0, 1, 0, 0, 0, 0,          0],
                      [ 0, 0, 0,  0, 0, 0,  0, 0, 1, 0, 0, 0,          0],
                      [ c, s, 0,  0, 0, 0,  0, 0, 0, 1, 0, 0, -x1*s+y1*c],
                      [-s, c, 0,  0, 0, 0,  0, 0, 0, 0, 1, 0, -x1*c-y1*s],
                      [ 0, 0, 1,  0, 0, 0,  0, 0, 0, 0, 0, 1,          0],
                      [ 0, 0, 0,  c, s, 0,  0, 0, 0, 1, 0, 0, -x2*s+y2*c],
                      [ 0, 0, 0, -s, c, 0,  0, 0, 0, 0, 1, 0, -x2*c-y2*s],
                      [ 0, 0, 0,  0, 0, 1,  0, 0, 0, 0, 0, 1,          0],
                      [ 0, 0, 0,  0, 0, 0,  c, s, 0, 1, 0, 0, -x3*s+y3*c],
                      [ 0, 0, 0,  0, 0, 0, -s, c, 0, 0, 1, 0, -x3*c-y3*s],
                      [ 0, 0, 0,  0, 0, 0,  0, 0, 1, 0, 0, 1,          0]], dtype=float)

        dx = np.linalg.inv(A.T @ A) @ A.T @ dy
        x += dx

        if np.linalg.norm(dx[9:12]) < 1e-4 and abs(dx[12, 0]) < 1e-6:
            break

    state.P1 = Point(x[0,0], x[1,0], x[2,0])
    state.P2 = Point(x[3,0], x[4,0], x[5,0])
    state.P3 = Point(x[6,0], x[7,0], x[8,0])

    position = Point(float(-x[9,0]), float(-x[10,0]), float(-x[11,0]))
    orientation = x[12,0]
    state.tachy_2.set_station(position, orientation)

    return position, orientation



def calculate_image_trafo():

    if not all([state.P1, state.P2, state.P3]):
        return False

    P1_vector = np.array([state.P1.X, state.P1.Y, state.P1.Z], dtype=float)
    P2_vector = np.array([state.P2.X, state.P2.Y, state.P2.Z], dtype=float)
    P3_vector = np.array([state.P3.X, state.P3.Y, state.P3.Z], dtype=float)

    # new Y-axis
    Y = P2_vector - P1_vector
    state.s = np.linalg.norm(Y)
    if state.s == 0:
        raise ValueError("R1 und R2 dürfen nicht identisch sein.")
    Y /= state.s

    # new Z-axis
    Z = np.cross(P3_vector - P1_vector, Y)
    Z_length = np.linalg.norm(Z)
    if Z_length == 0:
        raise ValueError("R1, R2 und R3 dürfen nicht auf einer Linie liegen.")
    Z /= Z_length

    # new X-axis
    X = np.cross(Y, Z)
    X /= np.linalg.norm(X)

    # rotation matrix
    state.R = np.column_stack((X, Y, Z)).copy()

    # translation vector
    state.t = P1_vector.reshape(-1,1).copy()

    return True



### DRAWING ###

def transform_line(line: Line):

    transformed_line = Line(line.number,[])
    for point in line.points:
        xyz = np.array([point.X,point.Y,point.Z]).reshape(-1,1)
        XYZ = (state.s * (state.R @ xyz) + state.t).flatten()
        transformed_line.points.append(Point(XYZ[0],XYZ[1],XYZ[2],point.number))

    return transformed_line


async def draw_line(line: Line, offset=1):
    
    state.drawing = True

    # transform points
    line = transform_line(line)

    # 
    start_point = line.points[0]

    state.tachy_2.fast_aim_at(start_point)
    state.tachy_2.laser_on()

    start_point.Z += state.rover_prism_height
    state.tachy_1.fast_aim_at(start_point)

    #
    while state.drawing == True:

        # lock prism
        task = asyncio.create_task(state.tachy_2.lock_on_prism())

        await task

        state.tachy_1.start_continues_measurement(state.rover_prism_t)

        # drawing
        while state.tachy_1._locked == True:

            position = state.tachy_1.read_measurement_data()

            if position:
                position.Z -= state.rover_prism_height
                index, nearest = position.nearest(line.points)

                if line.points[-1].distance(position) < 0.02:
                    state.drawing = False
                    break

                new_index = min([len(line.points)-1, index+state.index_offset])
                state.tachy_2.aim_at(line.points[new_index])

        state.tachy_1.stop_continues_measurement()

        state.tachy_2.laser_off()
             