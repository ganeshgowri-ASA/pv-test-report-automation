"""Equipment integration interfaces"""

from .base import BaseInstrument
from .megohmmeter import Megohmmeter, MegohmeterSimulator

__all__ = [
    "BaseInstrument",
    "Megohmmeter",
    "MegohmeterSimulator",
]
