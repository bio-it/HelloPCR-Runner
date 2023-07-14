import sys
from cx_Freeze import setup, Executable

exe = [Executable("HelloPCR-Runner.py", icon='bioduolab.ico', base=None)]

include_files = ['./src/dshow_cam_control/lib/DexterLib.idl', './src/dshow_cam_control/lib/DexterLib.tlb', './src/dshow_cam_control/lib/DirectShow.tlb', 'mask.npy']
include_modules = ['contourpy', 'matplotlib', 'numpy', 'pyparsing', 'numpy', 'cv2', 'serial']
build_options = {'build_exe' : {'packages' : include_modules, 'include_files' : include_files}}

# 'HelloPCR additional hardware controll program'
setup(
    name = 'HelloPCR-Runner',
    version = '1.0.0',
    author='KBH, YSH',
    description = 'HelloPCR runner',
    options = build_options,
    executables=exe
)
