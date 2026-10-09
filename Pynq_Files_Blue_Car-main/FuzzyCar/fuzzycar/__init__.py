# FuzzyCar package initialization
from .sensors.maxsonar import MAXSONAR
from .sensors.PMOD_ACL2 import PMOD_ACL2
from .processing.Velocity import Velocity
from .coms.i2cpmod import I2CPMOD
from .coms.UartAXI import UartAXI
from .coms.SPIController import SPIController
from .coms.PWMController import PWMController
from .car.car import Car
# Package version
__version__ = "0.1.0"

# List of public modules
__all__ = [
    'MAXSONAR',
    'PMOD_ACL2',
    'Velocity',
    'I2CPMOD',
    'UartAXI',
    'SPIController',
    'PWMController',
    'car'
    
]
