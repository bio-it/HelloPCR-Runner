import os 
from comtypes import client, COMError

_modules = list(map(client.GetModule, ["./lib/DirectShow.tlb", "./lib/DexterLib.tlb"]))