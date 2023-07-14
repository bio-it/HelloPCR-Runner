import sys
import struct 
import argparse
import traceback
from src.common import *
from socketserver import TCPServer, BaseRequestHandler
import threading 
# Parsing args
parser = argparse.ArgumentParser()

parser.add_argument('-e', '-E', '--emulate', dest='EMULATOR', action="store_true", help='emulator mode')
parser.add_argument('-p', '--port', dest='port',type=int, help='TCP port number', default=48888)
parser.add_argument('serial', type=str, help='serial number')

args = parser.parse_args()

# Check serial number is valid
if len(args.serial) != 5:
    raise SystemExit('Serial number must be 5 characters')

SERIAL_NUMBER = 'HelloPCR%s' %args.serial

# Setup logger
from src.logger import set_loggers, server_logger
set_loggers(SERIAL_NUMBER)

# Server ip & port declares
HOST = '127.0.0.1'
PORT = args.port

error_code = ErrorCode._
error_message = ''
server_running = True

def init_device():
    global error_code, error_message
    try:
        serial_task, shot_worker = None, None
        if args.EMULATOR:
            from emulator.shot_worker import ShotEmulator
            from emulator.serial_task import SerialEmulator, DeviceState
            serial_task = SerialEmulator()
            shot_worker = ShotEmulator()
        else:
            from src.shot_worker import ShotWorker
            from src.serial_task import SerialTask
            serial_task = SerialTask(serial_number=SERIAL_NUMBER)
            shot_worker = ShotWorker(serial_number=SERIAL_NUMBER, serial_task=serial_task)
        shot_worker.start()
        return serial_task, shot_worker
    except SerialNotDetectedError as e:
        error_code = ErrorCode.SerialError
        error_message = str(e)
    except CameraNotDetectedError as e:
        error_code = ErrorCode.CameraError
        error_message = str(e)
    except ShotWorkerError as e:
        error_code = ErrorCode.ShotWorkerError
        error_message = str(e)
    except BaseException as e:
        error_code = 0x10 + ErrorCode.UnknownError
        error_message = 'Software error'
        server_logger.error(f'Unknown exception : {e}')
        server_logger.error(traceback.format_exc())
    return None, None

serial_task, shot_worker = init_device()
class CommandHandler(BaseRequestHandler):
    def command_handler(self, command:int, filter_index:int, 
                        current_cycle:int, experiment_date:str):
        global server_running
        global error_code, error_message
        intensity = -1
        try:
            if command == Command.EXIT: 
                server_logger.info('server recv exit command')
                server_running = False
            elif error_code != ErrorCode._: return
            elif command == Command.STATUS: 
                serial_task.get_excitation_led()
                intensity = shot_worker.get_intensity()
            elif command == Command.SHOT:
                shot_worker.shot(filter_index, current_cycle, experiment_date)
            elif command in [ Command.OFF, Command.READY, Command.RUN, Command.ERROR ]:
                serial_task.set_device_state(INDICATOR[command])
            else: raise CommandNotDefinedError("")
        except CommandNotDefinedError as e:
            error_code = ErrorCode.ServerError
            error_message = f'({str(e)})'
            server_logger.error(error_message)
        except SerialDisconnectedError as e:
            error_code = ErrorCode.SerialError
            error_message = str(e)
        except CameraDisconnectedError as e:
            error_code = ErrorCode.CameraError
            error_message = str(e)
        except ShotWorkerError as e:
            error_code = ErrorCode.ShotWorkerError
            error_message = str(e)
        except OSError as e:
            server_logger.info(f'disconnected {str(e)}')
        except BaseException as e:
            error_code = ErrorCode.UnknownError
            error_message = "Software error"
            server_logger.error(f'Unknown exception : {error_message}')
            server_logger.error(traceback.format_exc())
        finally:
            if error_code not in [ErrorCode._, ErrorCode.SerialError]:
                serial_task.set_device_state(DeviceState.ERROR)
            return intensity
    
    def handle(self):
        global server_running
        global serial_task, shot_worker
        global error_code, error_message
        try:
            serial_task.set_device_state(DeviceState.READY)
            while server_running:
                intensity = -1
                raw_data = self.request.recv(BUFFER_SIZE)
                if len(raw_data) == 0: break # connection broken
                command, filter_index, current_cycle, experiment_date, _ = struct.unpack('3B15s110s', raw_data)
                experiment_date = experiment_date.decode('utf8')
                if error_code == ErrorCode._: # check error occurred
                    intensity = self.command_handler(command, filter_index, current_cycle,experiment_date)
                if command == Command.STATUS: # only response status command
                    response = struct.pack('=Bi100s', error_code, intensity, error_message.encode())
                    self.request.send(response)
            server_logger.info('Server command handling loop done.')
        except KeyboardInterrupt: 
            server_logger.info('Keyboard interrupt')
        except OSError as e:
            server_logger.info(f'Disconnected {str(e)}')
        except BaseException as e:
            server_logger.error(f'Unknown exception {str(e)}')
        finally: 
            if error_code != ErrorCode.SerialError:
                if serial_task:serial_task.set_device_state(DeviceState.OFF)
            raise SystemExit('Terminate Server...')



if __name__ == '__main__':
    server = TCPServer((HOST, PORT), CommandHandler)
    try:
        server.serve_forever()
    except SystemExit as e:
        server_logger.info(str(e))
    except BaseException as e:
        server_logger.error(str(e))
    finally:
        if shot_worker is not None: shot_worker.close()
        if serial_task is not None: serial_task.close()
        server.server_close()