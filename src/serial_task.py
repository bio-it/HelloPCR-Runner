import time
import serial
from serial import Serial
from serial.tools import list_ports
from src.common import LED_PWM, VID, PID, DeviceState
from src.common import SerialNotDetectedError, SerialDisconnectedError
from src.logger import serial_logger

def get_valid_ports():
    """ COM port filtering using vid(0x239A) & pid(0x801E) """
    return [port.name for port in list_ports.comports() if port.vid == VID and port.pid == PID]

class SerialTask:
    def __init__(self, serial_number:str):
        self.serial_number = serial_number
        self.device = self.get_device(serial_number)
        serial_logger.info(f"Successfully connected serial device")

        # initial led setttings
        self.set_led_pwm(250)
        self.set_excitation_led(False)

    def get_device(self, serial_number:str):
        device:Serial = None

        # find valid port_name
        for port_name in get_valid_ports():
            device:Serial

            try:
                device = Serial(port_name, 9600)
            except serial.SerialException as e:
                serial_logger.debug(f"{port_name} is already opened")
                continue

            device.write('v'.encode())
            while not device.in_waiting: pass

            val = device.readline().decode().strip()
            if val == serial_number: return device

            device.close()
        
        serial_logger.error(f"Cannot found serial deivce")
        raise SerialNotDetectedError()

    
    def flush(self):
        """ Flush Rx buffers """
        while self.device.in_waiting > 0: # flush
            self.device.readline()

    def __write(self, cmd):
        """ Write Tx buffer """
        try:
            cmd = cmd+'\r\n'
            self.device.write(cmd.encode())
        except Exception as e:

            serial_logger.error(f"Disconnected to serial device")
            raise SerialDisconnectedError()

    def __read(self):
        """ Read Rx buffer """
        try:
            res = self.device.readline()
        except Exception as e:
            serial_logger.error(f"Disconnected to serial device")
            raise SerialDisconnectedError()

        return res.decode().strip()

    def set_led_pwm(self, led_pwm:int) -> None:
        self.__write(f'P {led_pwm}')
        serial_logger.debug(f"set LED PWM value {led_pwm}")

    def get_led_pwm(self) -> int:
        self.__write('p')
        res = self.__read()
        return int(res)
    
    def set_excitation_led(self, state:bool) -> None:
        self.__write(f'E {int(state)}')
        serial_logger.debug(f"set LED on/off {state}")

    def get_excitation_led(self) -> int:
        self.__write(f'e')
        res = self.__read()
        return int(res)

    def set_device_state(self, state):
        self.__write(f'I {state}')
        serial_logger.info(f'device state : {DeviceState(state)}')

    def get_device_state(self):
        self.__write(f'i')
        res = self.__read()
        return int(res)
    
    def get_reference_position(self):
        """ load heater pattern right shoulder position from arduino firmware """
        self.__write('m')
        res = self.__read()
        x,y = res.split(' ')
        return int(x), int(y)
    
    def close(self):
        self.device.close()