name = "qumquat"

from .main import Qumquat
import sys
sys.modules[__name__] = Qumquat()
