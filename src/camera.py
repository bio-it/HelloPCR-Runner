import cv2
import threading
from comtypes import COMError
from src.dshow_cam_control.dshow_cam_ctrl import *
from src.common import FRAME_WIDTH, FRAME_HEIGHT, EXPOSURE, FOCUS, GAIN, GAMMA, WHITEBALACE, LOW_LIGHT_COMPENSATION
from src.common import CameraNotDetectedError, CameraDisconnectedError
from src.logger import camera_logger


class CameraBufferCleaner(threading.Thread):
    """ Camera worker class """
    def __init__(self, serial_number=""):
        threading.Thread.__init__(self) 
        self.daemon = True

        self.error = None

        self.stop_flag = False
        self.last_frame = None

        self.serial_number = serial_number

        try:
            filters_dict = get_device_filter_dict()

            self.cam_p_moniker  = filters_dict[self.serial_number]
            self.cam_no         = list(filters_dict.keys()).index(self.serial_number)
        except Exception:
            camera_logger.error(f"Cannot found camera")
            raise CameraNotDetectedError()
        
        self.cap = cv2.VideoCapture(self.cam_no, cv2.CAP_DSHOW)
        camera_logger.info(f"Successfully connected camera" )
    
    # Camera setup fuctions
    def setup_cam_all(self, focus, exposure, gain, gamma, low_light_com, white_balance):
        camera_logger.debug(f"Start setup camera")
        
        try:
            setup_cam(self.cam_p_moniker,
                    focus         = focus,
                    exposure      = exposure,
                    gain          = gain,
                    gamma         = gamma,
                    low_light_com = low_light_com,
                    white_balance = white_balance)
        except BaseException:
            camera_logger.error(f"Camera parameters setting error")
            self.error =  CameraDisconnectedError()
        except Exception:
            pass
        camera_logger.debug(f"Setup done camera {get_all_settings(self.cam_p_moniker)}")


    def set_focus(self, focus):
        set_focus(self.cam_p_moniker, focus)

    def set_exposure(self, exposure):
        set_exposure(self.cam_p_moniker, exposure)

    def set_lowlight_compensation(self, low_light_com):
        set_lowlight_compensation(self.cam_p_moniker, low_light_com)

    def set_whitebalance(self, white_balance):
        set_whitebalance(self.cam_p_moniker, white_balance)

    def get_all_settings(self):
        return get_all_settings(self.cam_p_moniker)
    
    def get_frame(self):
        if self.error is not None:
            raise self.error
        return self.last_frame
        
    def run(self):
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            camera_logger.debug(f"Resolution setup done {FRAME_WIDTH}x{FRAME_HEIGHT}")
        
            self.setup_cam_all(
                focus         = FOCUS,
                exposure      = EXPOSURE,
                gain          = GAIN,
                gamma         = GAMMA,
                low_light_com = LOW_LIGHT_COMPENSATION,
                white_balance = WHITEBALACE)
        except BaseException:
            camera_logger.error(f"Camera parameters setting error")
            self.error = Exception(f"Camera parameters setting error")
            
        camera_logger.debug("Start camera read")
        try:
            while not self.stop_flag:
                ret, self.last_frame = self.cap.read()    
                
                if not ret:
                    raise CameraDisconnectedError()
        except BaseException as e :
            camera_logger.error(f"Disconnected to camera")
            self.error = CameraDisconnectedError()
        
    def close(self):
        camera_logger.debug(f"Start close camera thread")
        self.stop_flag = True
        self.cap.release()
        camera_logger.debug(f"Camera close done")