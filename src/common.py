import os
from enum import IntEnum

''' Error Code '''

class ErrorCode(IntEnum):
    _               = 0x00
    ServerError     = 0x01,
    CameraError     = 0x02,
    SerialError     = 0x03,
    ShotWorkerError = 0x04,
    UnknownError    = 0x0F

''' Server Exceptions '''

class CommandNotDefinedError(Exception):
    def __init__(self):
        super().__init__('Command not defined')

''' Shot Worker Parameters and Exception Class '''

FLUORESCENCE = ['FAM', 'HEX', 'ROX', 'CY5']

FLUOR_CHANNEL = {
    'FAM' : 1, # FAM
    'HEX' : 1, # HEX
    'ROX' : 2, # ROX
    'CY5' : 2, # CY5
}
MASK_PATH = os.path.join(os.getcwd(), 'mask.npy')

class ShotWorkerError(Exception):
    def __init__(self, message):
        super().__init__(message)

''' Serial Task Parameters '''

# LED PWM declare
LED_PWM = 250

# Trinket M0 VID, PID
VID = 0x239A
PID = 0x801E


class DeviceState(IntEnum):
    """ Device states for control presentation LED """
    OFF     = 0x00,
    READY   = 0x01,
    RUNNING = 0x02,
    ERROR   = 0x03

class SerialNotDetectedError(Exception):
    def __init__(self):
        super().__init__(f"not found device")

class SerialDisconnectedError(Exception):
    def __init__(self):
        super().__init__(f"Device disconnected")


'''Camera Parameters and Exception Class'''

FRAME_WIDTH             = 2592
FRAME_HEIGHT            = 1944

EXPOSURE                = -1
FOCUS                   = 1023
GAIN                    = 20
GAMMA                   = 72
WHITEBALACE             = 4000
LOW_LIGHT_COMPENSATION  = False

ROI_AREA = {
    'dx' : 325,
    'dy' : 132,
    'width' : 420,
    'height': 560,
}

class CameraNotDetectedError(Exception):
    def __init__(self):
        super().__init__("not found camera")

class CameraDisconnectedError(Exception):
    def __init__(self):
        super().__init__("Camera disconnected")

''' TCP Server Parameters '''

class Command(IntEnum):
    STATUS  = 0x00,
    SHOT    = 0x01,
    OFF     = 0x02,
    READY   = 0x03,
    RUN     = 0x04,
    ERROR   = 0x05,
    EXIT    = 0xFF,

BUFFER_SIZE = 128

INDICATOR = { 
    Command.OFF : DeviceState.OFF, 
    Command.READY : DeviceState.READY, 
    Command.RUN : DeviceState.RUNNING, 
    Command.ERROR : DeviceState.ERROR
    }