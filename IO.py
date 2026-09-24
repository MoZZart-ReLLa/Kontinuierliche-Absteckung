import serial
import serial.tools.list_ports
from models import *
import math
import time



#### SERIAL COMMUNICATION CODES ###

GRC_OK = "%R1P,0,0:0"

TMC_GetFace = "%R1Q,2026:"
AUT_ChangeFace = "%R1Q,9028:0,0,0"
TMC_FACE_1 = "%R1P,0,0:0,0"
TMC_FACE_2 = "%R1P,0,0:0,1"

EDM_LASER_ON = "%R1Q,1004:1"
EDM_LASER_OFF = "%R1Q,1004:0"

AUT_MakePositioning = "%R1Q,9027:{},{}"

TMC_GetSimpleMea = "%R1Q,2108:1"
TMC_GetCoordinate = "%R1Q,2082:{},1"
TMC_DoMeasure = "%R1Q,2008:1,1"
TMC_GetAngle5 = "%R1Q,2107:1"

TMC_SetEdmMode = "%R1Q,2020:{}"
BAP_SetPrismType = "%R1Q,17008:{}"
TMC_SetStation = "%R1Q,2010:{},{},{},0"
TMC_SetOrientation = "%R1Q,2113:{}"

MOT_StartController = "%R1Q,6001:{}"
MOT_StopController = "%R1Q,6002:0"
MOT_StartVelocity = "%R1Q,6004:{},{}"

AUT_FineAdjust = "%R1Q,9037:{},{}"





### Tachyometer Class ###

class Tachy:


    ### SERIAL COMMUNICATION SETTINGS ###

    def __init__(self, port: str):

        self.port = port
        self.serial_connection = serial.Serial(self.port, 19200, timeout=10)

        self.position = Point(0, 0, 0)
        self.geocom(TMC_SetStation.format(0,0,0))
        
        self.laser_on()
        

    def geocom(self, command: str):

        full_cmd = f"{command}\r\n"
        self.serial_connection.write(full_cmd.encode("ascii"))

        response = self.serial_connection.read_until().decode("ascii").strip()

        #print(f"Command: {command} | Response: {response}")

        return response


    def stop(self):

        self.geocom(MOT_StartController.format(2))
        self.laser_off()




    ### DEVICE SETTINGS ###

    def set_station(self, position: Point, hz_correction: float):

        self.position = position
        res = self.geocom(TMC_SetStation.format(position.X, position.Y, position.Z))

        hz, v = self.angle_measurement()
        res = self.geocom(TMC_SetOrientation.format(hz - hz_correction))




    ### DEVICE CONTROL COMMANDS ###

    def face_one(self):

        if self.geocom(TMC_GetFace) == TMC_FACE_2:
            self.geocom(AUT_ChangeFace)

    def face_two(self):

        if self.geocom(TMC_GetFace) == TMC_FACE_1:
            self.geocom(AUT_ChangeFace)


    def fast_aim_at(self, P: Point):

        delta_x = P.X - self.position.X
        delta_y = P.Y - self.position.Y
        delta_z = P.Z - self.position.Z

        hz = math.atan2(delta_x, delta_y) % (2 * math.pi)
        v = math.atan2(math.hypot(delta_x, delta_y), delta_z)

        self.geocom(AUT_MakePositioning.format(hz, v))


    def aim_at(self, P: Point, tolerance=1e-3, max_speed=0.2, k_p=2.0):
        
        delta_x = P.X - self.position.X
        delta_y = P.Y - self.position.Y
        delta_z = P.Z - self.position.Z

        target_hz = math.atan2(delta_x, delta_y) % (2 * math.pi)
        target_v = math.atan2(math.hypot(delta_x, delta_y), delta_z)

        self.geocom(MOT_StartController.format(1))

        while True:
            hz, v = self.angle_measurement()

            diff_hz = (target_hz - hz + math.pi) % (2 * math.pi) - math.pi
            diff_v = target_v - v

            if math.hypot(diff_hz, diff_v) < tolerance:
                break

            vel_hz = max(-max_speed, min(max_speed, k_p * diff_hz))
            vel_v = max(-max_speed, min(max_speed, k_p * diff_v))

            self.geocom(MOT_StartVelocity.format(vel_hz, vel_v))
            time.sleep(0.05)

        self.geocom(MOT_StartController.format(2))




    ### DATA RETRIEVAL COMMANDS ###

    def single_measurement(self, prism_type: BAP_PRISMTYPE):

        # settings
        if prism_type:
            self.geocom(TMC_SetEdmMode.format(2))
            self.geocom(BAP_SetPrismType.format(prism_type))
            self.geocom(AUT_FineAdjust.format(0,0))
        else:
            self.geocom(TMC_SetEdmMode.format(5))

        # measurment
        i = 0
        if self.geocom(TMC_DoMeasure) == GRC_OK:
            while i < 10:
                response = self.geocom(TMC_GetCoordinate.format(500))
                data = response.split(":", 1)[1].split(",")
                if data[0] == "0":
                    return Point(float(data[1]),float(data[2]),float(data[3]))
                i += 1

        return None


    def two_face_measurement(self, prism_type: BAP_PRISMTYPE):

        M1 = self.single_measurement(prism_type)
        if M1 != None:

            self.geocom(AUT_ChangeFace)
            M2 = self.single_measurement(prism_type)
            if M2 != None:
                return Point((M1.X+M2.X)/2, (M1.Y+M2.Y)/2, (M1.Z+M2.Z)/2)

        return None


    def angle_measurement(self):
        response = self.geocom(TMC_GetAngle5)
        data = response.split(":", 1)[1].split(",")

        hz = float(data[1])
        v = float(data[2])

        return hz, v



    ### TARGET TRACKING COMMANDS ###
        



    ### LASER CONTROL COMMANDS ###

    def laser_on(self):

        self.geocom(EDM_LASER_ON)


    def laser_off(self):

        self.geocom(EDM_LASER_OFF)