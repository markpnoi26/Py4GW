import inspect
import math
import sys
import time
import traceback
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from time import sleep

import Py2DRenderer
import PyAgent
import PyCamera
import PyEffects
import PyImGui
import PyInventory
import PyItem
import PyKeystroke
import PyMap
import PyMerchant
import PyMissionMap
import PyOverlay
import PyParty
import PyPathing
import PyPlayer
import PyQuest
import PySkill
import PySkillbar
import PyUIManager

import Py4GW

from .Agent import *
from .AgentArray import *
from .Camera import *
from .DXOverlay import *
from .Effect import *
from .enums import *
from .GlobalCache import GLOBAL_CACHE
from .IconsFontAwesome5 import *
from .ImGui import *
from .Inventory import *
from .Item import *
from .ItemArray import *
from .Map import *
from .Merchant import *
from .model_data import *
from .Overlay import *
from .Party import *
from .Player import *
from .Py4GWcorelib import *
from .Quest import *
from .Routines import *
from .Skill import *
from .Skillbar import *
from .SkillManager import *
from .UIManager import *

traceback = traceback
math = math
Enum = Enum

Py4Gw = Py4GW
PyImGui = PyImGui
PyMap = PyMap
PyMissionMap = PyMissionMap
PyAgent = PyAgent
PyPlayer = PyPlayer
PyParty = PyParty
PyItem = PyItem
PyInventory = PyInventory
PySkill = PySkill
PySkillbar = PySkillbar
PyMerchant = PyMerchant
PyEffects = PyEffects
#PyKeystroke = PyKeystroke
PyOverlay = PyOverlay
PyQuest = PyQuest
PyPathing = PyPathing
PyUIManager = PyUIManager
PyCamera = PyCamera
Py2DRenderer = Py2DRenderer
GLOBAL_CACHE = GLOBAL_CACHE

#redirect print output to Py4GW Console
class Py4GWLogger:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("print:", f"{message.strip()}", Py4GW.Console.MessageType.Info)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing
    
class Py4GWLoggerError:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("print:", f"{message.strip()}", Py4GW.Console.MessageType.Error)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing

# Redirect Python's print output to Py4GW Console
sys.stdout = Py4GWLogger()
sys.stderr = Py4GWLoggerError()