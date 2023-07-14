import time

from comtypes.gen.DirectShowLib import (
    ICreateDevEnum,
    IEnumMoniker,
    IBaseFilter,
    IAMCameraControl,
    IAMVideoProcAmp,
)
from comtypes.gen import DirectShowLib
from comtypes.persist import IPropertyBag
from comtypes import *

from src.logger import camera_logger


# values for tagCameraControlFlags enum
CameraControl_Flags_Auto    = c_long(1)
CameraControl_Flags_Manual  = c_long(2)

# values for tagCameraControlProperty enum
CameraControl_Pan       = c_long(0)
CameraControl_Tilt      = c_long(1)
CameraControl_Roll      = c_long(2)
CameraControl_Zoom      = c_long(3)
CameraControl_Exposure  = c_long(4)
CameraControl_Iris      = c_long(5)
CameraControl_Focus     = c_long(6)
CameraControl_LowLightCompensation = c_long(19)


# values for tagVideoProcAmpFlags enum
VideoProcAmp_Flags_Auto     = c_long(1)
VideoProcAmp_Flags_Manual   = c_long(2)

# values for tagVideoProcAmpProperty enum
VideoProcAmp_Brightness     = c_long(0)
VideoProcAmp_Contrast       = c_long(1)
VideoProcAmp_Hue            = c_long(2)
VideoProcAmp_Saturation     = c_long(3)
VideoProcAmp_Sharpness      = c_long(4)
VideoProcAmp_Gamma          = c_long(5)
VideoProcAmp_ColorEnable    = c_long(6)
VideoProcAmp_WhiteBalance   = c_long(7)
VideoProcAmp_BacklightCompensation = c_long(8)
VideoProcAmp_Gain           = c_long(9)


def get_device_filter_dict():
    """
    Return camera device names and moniker interfaces to dictionary type

    Returns:
        dict: {"dev_names" : POINTER(IMoniker), ...}
    """
    hr = CoInitialize()

    device_enum = client.CreateObject("{62BE5D10-60EB-11d0-BD3B-00A0C911CE86}", interface=ICreateDevEnum)
    moniker_enum = device_enum.CreateClassEnumerator(IID("{860BB310-5D01-11d0-BD3B-00A0C911CE86}"), dwFlags=0)
    
    cam_dict = {}
    while True:
        p_moniker, cnt = moniker_enum.RemoteNext(1)
        if not cnt: break
        
        try:
            p_prop_bag = p_moniker.RemoteBindToStorage(0, 0, IPropertyBag._iid_).QueryInterface(IPropertyBag)
            filter_name = p_prop_bag.Read("FriendlyName", pErrorLog=None)
        except Exception as err:
            camera_logger.error(camera_logger)
            raise err
            
        cam_dict[filter_name] = p_moniker
        
    if cam_dict:
        return cam_dict
    else:
        return None

    hr = CoUninitialize()
    

def set_cameraControl(p_moniker, property_, value, flag):
    """
    Set values to control camera using IAMCameraControl interface

    Args:
        p_moniker (POINTER(IMoniker)): moniker point of device
        property_ (c_long): Camera control property constant
        value (int): value
        flag (c_long): Auto/Manual Flag constant
    """
    p_cam_ctrl = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_).QueryInterface(IAMCameraControl)
    p_cam_ctrl.Set(property_, c_long(value), flag)

def set_videoProcAmp(p_moniker, property_, value, flag):
    """
    Set values to control camera using IAMVideoProcAmp interface

    Args:
        p_moniker (POINTER(IMoniker)): moniker point of device
        property_ (c_long): VideoProcAmp's constant
        value (int): value
        flag (c_long): Auto/Manual Flag constant
    """
    p_cam_ctrl = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_).QueryInterface(IAMVideoProcAmp)
    p_cam_ctrl.Set(property_, c_long(value), flag)

def get_all_settings(p_moniker):

    hr = CoInitialize()

    res = {}

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_cam_ctrl = p_cap.QueryInterface(IAMCameraControl)
    p_proc_amp = p_cap.QueryInterface(IAMVideoProcAmp)

    value, flag = c_long(), c_long()

    res["focus"]        = p_cam_ctrl.Get(CameraControl_Focus)
    res["exposure"]     = p_cam_ctrl.Get(CameraControl_Exposure)
    res["gain"]         = p_proc_amp.Get(VideoProcAmp_Gain)
    res["gamma"]        = p_proc_amp.Get(VideoProcAmp_Gamma)
    res["whilebalance"] = p_proc_amp.Get(VideoProcAmp_WhiteBalance)
    res["low_light_com"]= p_cam_ctrl.Get(CameraControl_LowLightCompensation)


    hr = CoUninitialize()

    return res

    
def setup_cam(p_moniker, focus, exposure, gain, gamma, low_light_com, white_balance):
    """
    Set focus, exposure, low-light-compensation, white-balance to control "Arducam IMX298"

    Args:
        p_moniker (POINTER(IMoniker)): _description_
        focus (int): foucs value
        exposure (int): exposure value
        low_light_com (int): low-light-compensation value (0:off, 1:on)
        white_balance (int): white-balance value
    """
    hr = CoInitialize()

    # Get pointers (IAMCameraControl, IAMVideoProcAmp)
    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_cam_ctrl = p_cap.QueryInterface(IAMCameraControl)
    p_proc_amp = p_cap.QueryInterface(IAMVideoProcAmp)
    
    # Setup Low-light-compensation
    p_cam_ctrl.Set(CameraControl_LowLightCompensation, c_long(low_light_com), CameraControl_Flags_Manual)
    # time.sleep(0.5)
    
    # Setup Focus
    # Need (v-1)Auto -> (v-1)Manual -> (v)Manual
    p_cam_ctrl.Set(CameraControl_Focus, c_long(focus-1), CameraControl_Flags_Auto)
    time.sleep(0.5)
    p_cam_ctrl.Set(CameraControl_Focus, c_long(focus-1), CameraControl_Flags_Manual)
    time.sleep(0.5)
    p_cam_ctrl.Set(CameraControl_Focus, c_long(focus), CameraControl_Flags_Manual)
    
    # Setup Exposure
    # Need (v)Auto -> (v)Manual
    p_cam_ctrl.Set(CameraControl_Exposure, c_long(exposure), CameraControl_Flags_Auto)
    time.sleep(0.5)
    p_cam_ctrl.Set(CameraControl_Exposure, c_long(exposure), CameraControl_Flags_Manual)
    time.sleep(0.5)

    # Setup White-balance
    p_proc_amp.Set(VideoProcAmp_WhiteBalance, c_long(white_balance), VideoProcAmp_Flags_Manual)

    # Setup gamma
    p_proc_amp.Set(VideoProcAmp_Gamma, c_long(gamma), VideoProcAmp_Flags_Manual)

    # Setup gain
    p_proc_amp.Set(VideoProcAmp_Gain, c_long(gain), VideoProcAmp_Flags_Manual)
    



    hr = CoUninitialize()

def set_focus(p_moniker, focus):
    hr = CoInitialize()

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_cam_ctrl = p_cap.QueryInterface(IAMCameraControl)
    
    # Setup Focus
    # Need (v-1)Auto -> (v-1)Manual -> (v)Manual
    p_cam_ctrl.Set(CameraControl_Focus, c_long(focus-1), CameraControl_Flags_Auto)
    time.sleep(0.5)
    p_cam_ctrl.Set(CameraControl_Focus, c_long(focus-1), CameraControl_Flags_Manual)
    time.sleep(0.5)
    p_cam_ctrl.Set(CameraControl_Focus, c_long(focus), CameraControl_Flags_Manual)

    camera_logger.debug(f"focus setting done {focus}")

    hr = CoUninitialize()

def set_exposure(p_moniker, exposure):
    hr = CoInitialize()

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_cam_ctrl = p_cap.QueryInterface(IAMCameraControl)

    # Setup Exposure
    # Need (v)Auto -> (v)Manual
    p_cam_ctrl.Set(CameraControl_Exposure, c_long(exposure), CameraControl_Flags_Auto)
    time.sleep(0.5)
    p_cam_ctrl.Set(CameraControl_Exposure, c_long(exposure), CameraControl_Flags_Manual)
    time.sleep(0.5)

    hr = CoUninitialize()

def set_lowlight_compensation(p_moniker, low_light_com):
    hr = CoInitialize()

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_cam_ctrl = p_cap.QueryInterface(IAMCameraControl)

    # Setup Low-light-compensation
    p_cam_ctrl.Set(CameraControl_LowLightCompensation, c_long(low_light_com), CameraControl_Flags_Manual)
    time.sleep(0.5)

    hr = CoUninitialize()

def set_whitebalance(p_moniker, white_balance):
    hr = CoInitialize()

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_proc_amp = p_cap.QueryInterface(IAMVideoProcAmp)

    # Setup White-balance
    p_proc_amp.Set(VideoProcAmp_WhiteBalance, c_long(white_balance), VideoProcAmp_Flags_Manual)

    hr = CoUninitialize()

def set_gamma(p_moniker, gamma):
    hr = CoInitialize()

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_proc_amp = p_cap.QueryInterface(IAMVideoProcAmp)

    # Setup gamma
    p_proc_amp.Set(VideoProcAmp_Gamma, c_long(gamma), VideoProcAmp_Flags_Manual)

    hr = CoUninitialize()


def set_gain(p_moniker, gain):
    hr = CoInitialize()

    p_cap = p_moniker.RemoteBindToObject(0, 0, IBaseFilter._iid_)
    p_proc_amp = p_cap.QueryInterface(IAMVideoProcAmp)

    # Setup gain
    p_proc_amp.Set(VideoProcAmp_Gain, c_long(gain), VideoProcAmp_Flags_Manual)

    hr = CoUninitialize()