import os
import cv2
import time
import datetime
import threading
import numpy as np
from comtypes import COMError
from src.serial_task import SerialTask
from src.camera import CameraBufferCleaner as Camera
from src.logger import shot_logger
from src.common import FOCUS, ROI_AREA, MASK_PATH, FRAME_WIDTH, FRAME_HEIGHT, FLUORESCENCE, FLUOR_CHANNEL, ShotWorkerError

class ShotWorker(threading.Thread):
    def __init__(self, serial_number: str, serial_task: SerialTask):
        threading.Thread.__init__(self) 
        self.daemon:bool = True
        
        self.cycle:int = -1
        self.fluorescence:str = 'FAM'
        self.intensity:int = -1
        self.running:threading.Event = threading.Event()
        self.serial_number = serial_number
        self.serial_task:SerialTask = serial_task
        self.camera:Camera = Camera(serial_number)
        
        self.error = None

        _x, _y = self.serial_task.get_reference_position()
        self.pos_roi = (_y - ROI_AREA['dy'], _x - ROI_AREA['dx'])
        

        try:
            self.mask = np.load(MASK_PATH)
        except Exception as e:
            shot_logger.error(f"Cannot loaded mask file {e}")
            raise ShotWorkerError("Cannot loaded mask file")
        
        if (self.mask.shape[0] != ROI_AREA["height"] or 
            self.mask.shape[1] !=  ROI_AREA["width"]):
            shot_logger.error(f"Invalid mask file")
            raise ShotWorkerError('Invalid mask file')

        shot_logger.debug(f"Successfully loaded mask file {np.unique(self.mask)}, {self.mask.shape}")

    def run(self):
        try:
            self.running.clear()
            self.camera.start()
            while True:
                self.running.wait()
                self.__shot()
        except COMError as error:
            shot_logger.error(error)
            self.error = ShotWorkerError(str(error))
        except BaseException as error:
            shot_logger.error(error)
            self.error = error
        
    def calc_intensity(self, image):
        image = image[:, :, FLUOR_CHANNEL[self.fluorescence]]
        intensity = np.mean(image[self.mask == 255])
        return int(intensity * 256) # Normalizing intensity (change 4096 -> 65500)
    
    def get_intensity(self):
        self.check_error()
        return self.intensity
    
    def camera_set_focus(self, focus, retry=5):
        for count in range(retry):
            try:
                self.camera.set_focus(focus)
                break
            except COMError as error:
                shot_logger.error(f'Camera set focus retry-{count+1}')
                shot_logger.error(error)
        if count+1 == retry:
            error = ShotWorkerError(f'Camera set focus retry failed')
            shot_logger.error(error)

    def __shot(self):
        start_time = time.perf_counter()

        # Set Camera Focus 
        self.camera_set_focus(FOCUS)

        # Set led PWM on
        self.serial_task.set_excitation_led(True)
        
        # Wait 2 seconds because of camera's exposure
        time.sleep(2)

        # Get image
        image = self.camera.get_frame().copy()

        # Crop image
        image = image[self.pos_roi[0]:self.pos_roi[0]+ROI_AREA['height'], self.pos_roi[1]:self.pos_roi[1]+ROI_AREA['width']]

        # Get intensity
        self.intensity = self.calc_intensity(image)

        # Set led PWM off
        self.serial_task.set_excitation_led(False)
        
        # running flag off:
        self.running.clear()

        shot_logger.debug(f"shot spend time : {time.perf_counter()-start_time}, intensity : {self.intensity}")
        
        self.save_img(image)

    def shot(self, fluor:str, cycle:int, experiment_date:str):
        self.experiment_date = experiment_date
        self.fluorescence = FLUORESCENCE[fluor]
        self.cycle = cycle

        # reset intensity
        self.intensity = -1

        # running flag on
        self.running.set()

    def save_img(self, img:np.ndarray):
        try:
            base_path = os.path.join(os.getcwd(), 'Record', self.serial_number, self.experiment_date)
            os.makedirs(base_path, exist_ok=True)

            cur_datetime = datetime.datetime.now().strftime("%H%M%S")
            path = os.path.join(base_path, f"{self.fluorescence}_{self.cycle}_{cur_datetime}.png")
            cv2.imwrite(path, img)
        except Exception as e:
            shot_logger.error(f"image save error : {e}")
            self.error = ShotWorkerError(str("image save error"))
        
        shot_logger.debug(f"saved image '{path}'")
    
    def check_error(self):
        if self.camera.error is not None:
            raise self.camera.error
        if self.error is not None:
            raise self.error

    def close(self):
        shot_logger.debug(f"shot close start")
        self.camera.close()
        