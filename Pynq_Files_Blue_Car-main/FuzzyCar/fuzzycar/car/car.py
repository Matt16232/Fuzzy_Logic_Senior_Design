from ..sensors.maxsonar import MAXSONAR 
from ..coms.PWMController import PWMController  
from ..coms.UartAXI import UartAXI  
from ..coms.SPIController import SPIController 
from pynq import Overlay, MMIO 

class Car:
    
    def __init__(self, ol: Overlay):
        """
        Initializes the car object with various controllers and sensors.
        
        Parameters:
        ol (Overlay): The PYNQ overlay object containing all peripherals.
        """
        try:
            # UART-based sensors
            self.passenger_com = UartAXI(ol.passenger_side.mmio.base_addr)
            self.driver_com = UartAXI(ol.driver_side.mmio.base_addr)
            self.front_com = UartAXI(ol.front_side.mmio.base_addr)
            self.drifront_com = UartAXI(ol.drifront.mmio.base_addr)
            self.pasfront_com = UartAXI(ol.pasfront.mmio.base_addr)
            self.drivback_com = UartAXI(ol.drivback.mmio.base_addr)
            self.pasback_com = UartAXI(ol.pasback.mmio.base_addr)

            # Initialize MAXSONAR sensors with the correct communication objects
            self.passenger = MAXSONAR(self.passenger_com)
            self.driver = MAXSONAR(self.driver_com)
            self.front = MAXSONAR(self.front_com)  
            self.drifront = MAXSONAR(self.drifront_com)  
            self.pasfront = MAXSONAR(self.pasfront_com)
            self.drivback = MAXSONAR(self.drivback_com)
            self.pasback = MAXSONAR(self.pasback_com)

            # SPI LoRa Communication
            self.lora = SPIController(ol.lora.mmio.base_addr)
            self.lora.configure()

            # Motor & Steering Control (PWM)
            self.steering = PWMController(ol, 'axi_timer_0')  # Steering motor
            self.motor = PWMController(ol, 'pwm')  # Drive motor

        except AttributeError as e:
            print(f"Initialization error: {e}")
            print(f"Check if the overlay has the expected IP cores.")
