import serial
import serial.tools.list_ports
from trafo import Point



#### SERIAL COMMUNICATION CODES ###

TMC_GetFace = "%R1Q,2026:"
AUT_ChangeFace = "%R1Q,9028:0,0,0"
TMC_FACE_1 = "%R1P,0,0:0,0"
TMC_FACE_2 = "%R1P,0,0:0,1"

EDM_LASER_ON = "%R1Q,1004:1"
EDM_LASER_OFF = "%R1Q,1004:0"

AUT_MakePositioning = "%R1Q,9027:{},{}"
TMC_GetSimpleMea = "%R1Q,2108:1"



### Tachyometer Class ###

class Tachy:


    ### SERIAL COMMUNICATION SETTINGS ###

    def __init__(self, vendor_id: int, product_id: int, serial_number: str = None):

        self.position = Point(0, 0, 0)

        self.port = None
        for port in serial.tools.list_ports.comports():
            if port.vid == vendor_id and port.pid == product_id:
                if serial_number is None or port.serial_number == serial_number:
                    self.port = port.device
                    break
  
        if self.port is None:
            raise Exception("Device not found.")

        self.serial_connection = serial.Serial(self.port, 19200, timeout=10)
    

    def geocom(self, command: str):

        full_cmd = f"{command}\r\n"
        self.serial_connection.write(full_cmd.encode("ascii"))

        response = self.serial_connection.read_until().decode("ascii").strip()

        print(f"Command: {command} | Response: {response}")

        return response




    ### DEVICE CONTROL COMMANDS ###

    def face_one(self):

        if self.geocom(TMC_GetFace) == TMC_FACE_2:
            self.geocom(AUT_ChangeFace)
        

    def aim_at(self, AZ: float, EL: float):
        
        self.geocom(AUT_MakePositioning.format(AZ, EL))


    def aim_at(self, P: Point):

        X = P.X - self.position.X
        Y = P.Y - self.position.Y
        Z = P.Z - self.position.Z

        AZ = math.atan2(Y, X)
        EL = math.atan2(Z, math.sqrt(X**2 + Y**2))

        self.aim_at(AZ, EL)




    ### DATA RETRIEVAL COMMANDS ###

    def single_measurement(self):

        response = self.geocom(TMC_GetSimpleMea)
        data = response.split(":", 1)[1].split(",")

        return Point(map(float, data[1:4]))




    ### TARGET TRACKING COMMANDS ###
        



    ### LASER CONTROL COMMANDS ###

    def laser_on(self):

        self.geocom(EDM_LASER_ON)


    def laser_off(self):

        self.geocom(EDM_LASER_OFF)