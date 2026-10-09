from pynq.overlays.base import BaseOverlay
from pynq.lib import MicroblazeLibrary
import time  

class I2CPMOD:
    def __init__(self, scl_pin, sda_pin, base, a_b=0):  
        self.PMOD_SDA_PIN = sda_pin
        self.PMOD_SCL_PIN = scl_pin
        self.a_b = a_b  
        
        # Initialize PYNQ overlay and I2C device
        self.base = base
        if self.a_b == 0:  
            self.iop = self.base.iop_pmoda
        else:             
            self.iop = self.base.iop_pmodb
        self.lib = MicroblazeLibrary(self.iop, ['i2c'])
        self.i2c_device = self.lib.i2c_open(self.PMOD_SDA_PIN, self.PMOD_SCL_PIN)
        
    def write_data(self, device_addr, register_addr, data):
        """Write data to I2C device"""
        buffer = bytearray(3)
        buffer[0] = register_addr  # Register address
        buffer[1] = (data >> 8) & 0xFF  # Data MSB
        buffer[2] = data & 0xFF  # Data LSB
        
        self.i2c_device.write(device_addr, buffer, len(buffer))
        time.sleep(10e-3)  # Delay for stability
        
    def read_data(self, device_addr, num_bytes=2):
        """Read data from I2C device"""
        buffer = bytearray(num_bytes)
        self.i2c_device.read(device_addr, buffer, num_bytes)
        if num_bytes == 2:
            return (buffer[0] << 8) | buffer[1]
        return buffer
    
    def close(self):
        """Close I2C device"""
        self.i2c_device.close()

