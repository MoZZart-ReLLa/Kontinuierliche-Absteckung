from IO import Tachy

TS16 = Tachy(0x0403,0x6001)
TS16.turn_direction(0,3.14159265/2)
TS16.single_measurement()
