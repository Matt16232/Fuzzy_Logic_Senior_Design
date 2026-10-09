from time import time, sleep

class MAXSONAR:
    def __init__(self, uart):
        """
        Initialize the Pmod Sonar interface.
        
        Parameters:
            uart (UartAXI): The UART interface instance to communicate with the sonar.
                           Should be configured for 9600 baud, 8N1.
        """
        self.uart = uart
        # Configure UART
        self.uart.baudrate = 9600
        self.uart.stopbits = 1
        self.uart.parity = 'N'
        self.uart.bits = 8
        
        # Initial power-up delay and calibration
        sleep(0.25)  # 250ms power-up time
        sleep(0.049)  # 49ms for calibration
        sleep(0.1)   # Additional 100ms waiting time
        

    def read_distance(self):
        """
        Reads the distance measurement from the PmodMAXSONAR sensor.
        Expects format: 'R' + three ASCII digits + carriage return.

        Returns:
            float: Distance in inches, or None if the response is invalid.
        """
        while True:  # Retry loop until valid data is returned
            response = []
            timeout = time() + 0.1 

            # Clear any stale data
            while self.uart.is_data_ready():
                self.uart.read(1)

            # Wait until the full 5 bytes are ready or timeout
            while len(response) < 5 and time() < timeout:
                if self.uart.is_data_ready():
                    byte = self.uart.read(1)[0]
                    response.append(byte)
                sleep(0.001)  # Small delay to prevent busy waiting

            # Validate response format
            if len(response) == 5 and response[0] == ord('R') and response[4] == 13:
                try:
                    # Extract distance from the ASCII response
                    distance_str = ''.join(chr(b) for b in response[1:4])
                    distance = int(distance_str)

                    # Validate range (6-255 inches according to docs)
                    if 6 <= distance <= 255:
                        return distance  # Successfully return the distance
                except ValueError:
                    pass  # Ignore invalid values and retry

            sleep(0.1)  # Small delay before retrying (optional)
            
    def read_continuous(self, num_readings=10, delay=0.049):
        """
        Takes multiple readings in continuous mode.
        
        Parameters:
            num_readings (int): Number of readings to take
            delay (float): Delay between readings (49ms minimum according to docs)
            
        Returns:
            list: List of distance readings in inches
        """
        readings = []
        for _ in range(num_readings):
            distance = self.read_distance()
            if distance is not None:
                readings.append(distance)
            sleep(max(0.049, delay))  # Ensure minimum 49ms between readings
        return readings