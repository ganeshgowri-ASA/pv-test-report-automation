"""
IEC Protocol Implementations
Complete implementation of 8 IEC standards for PV module testing
"""

from .base import ProtocolBase, TestSequence, TestResult
from .iec_61215 import IEC61215Protocol
from .iec_61730 import IEC61730Protocol
from .iec_61853 import IEC61853Protocol
from .iec_62716 import IEC62716Protocol
from .iec_61701 import IEC61701Protocol
from .iec_62804 import IEC62804Protocol
from .iec_60904 import IEC60904Protocol
from .iec_62759 import IEC62759Protocol

__all__ = [
    'ProtocolBase',
    'TestSequence',
    'TestResult',
    'IEC61215Protocol',
    'IEC61730Protocol',
    'IEC61853Protocol',
    'IEC62716Protocol',
    'IEC61701Protocol',
    'IEC62804Protocol',
    'IEC60904Protocol',
    'IEC62759Protocol',
    'get_protocol',
    'get_all_protocols',
]

# Protocol registry
PROTOCOLS = {
    'IEC 61215': IEC61215Protocol,
    'IEC 61730': IEC61730Protocol,
    'IEC 61853': IEC61853Protocol,
    'IEC 62716': IEC62716Protocol,
    'IEC 61701': IEC61701Protocol,
    'IEC 62804': IEC62804Protocol,
    'IEC 60904': IEC60904Protocol,
    'IEC 62759': IEC62759Protocol,
}


def get_protocol(protocol_name: str) -> ProtocolBase:
    """Get protocol instance by name"""
    protocol_class = PROTOCOLS.get(protocol_name)
    if not protocol_class:
        raise ValueError(f"Unknown protocol: {protocol_name}")
    return protocol_class()


def get_all_protocols() -> dict:
    """Get all available protocols"""
    return {name: cls() for name, cls in PROTOCOLS.items()}
