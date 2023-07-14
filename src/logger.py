import os
import datetime
import logging

# Loogers & level declares
root_logger = logging.getLogger(name="")
root_logger.setLevel(logging.INFO)

shot_logger = logging.getLogger(name="Shot")
shot_logger.setLevel(logging.DEBUG)
shot_logger.propagate=False

camera_logger = logging.getLogger(name="Camera")
camera_logger.setLevel(logging.DEBUG)
camera_logger.propagate=False

serial_logger = logging.getLogger(name="Serial")
serial_logger.setLevel(logging.DEBUG)
serial_logger.propagate=False

server_logger = logging.getLogger(name="Server")
server_logger.setLevel(logging.DEBUG)
server_logger.propagate=False


# Add handler & formatter to logger
def set_loggers(serial_number):
    # Set fomatter
    formatter = logging.Formatter(f"%(asctime)s\t{serial_number}\t%(name)s\t%(levelname)s\t%(message)s")

    # mkdir log directory
    base_path = os.path.join(os.getcwd(), 'Record', serial_number, 'Log')
    os.makedirs(base_path, exist_ok=True)
    
    # Set handler
    cur_datetime = datetime.datetime.now().strftime("%Y%m%d")
    log_filename = f"runner-{cur_datetime}.log"
    log_path     = os.path.join(base_path, log_filename)

    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(formatter)

    # Attach file handler
    root_logger.addHandler(file_handler)
    shot_logger.addHandler(file_handler)
    camera_logger.addHandler(file_handler)
    serial_logger.addHandler(file_handler)
    server_logger.addHandler(file_handler)

    
