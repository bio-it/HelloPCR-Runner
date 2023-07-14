from enum import IntEnum

class DeviceState(IntEnum):
    """ Device states for control presentation LED """
    READY   = 0x00
    RUNNING = 0x01
    ERROR   = 0x02

class SerialEmulator:
    def __init__(self, serial_number=''):
        self.state = 0
        self.serial_number =''

    def set_status(self, command):
        self.state = command
        return command
    
    def get_excitation_led(self):
        return 0
    
    def close(self):
        return