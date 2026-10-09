from pynq import MMIO
from time import time, sleep

class UartAXI:
    # Hardware Constants
    RX_FIFO = 0x00
    TX_FIFO = 0x04
    STAT_REG = 0x08
    CTRL_REG = 0x0C

    # Status Register Bit Positions
    RX_VALID = 0
    RX_FULL = 1
    TX_EMPTY = 2
    TX_FULL = 3
    IS_INTR = 4
    OVERRUN_ERR = 5
    FRAME_ERR = 6
    PARITY_ERR = 7

    # Control Register Bit Positions
    RST_TX = 0
    RST_RX = 1
    INTR_EN = 4

    def __init__(self, address):
        """
        Initialize the UART AXI interface.
        Parameters:
        - address (int): Base address of the AXI UART Lite module.
        """
        self.uart = MMIO(address, 0x10000, debug=False)
        self.address = address

    def setupCtrlReg(self):
        """
        Resets the FIFOs and disables interrupts.
        """
        # Reset RX and TX FIFOs
        self.uart.write(self.CTRL_REG, (1 << self.RST_TX) | (1 << self.RST_RX))
        sleep(1)  # Wait for reset
        self.uart.write(self.CTRL_REG, 0)  # Disable resets
        sleep(1)

    def read(self, count, timeout=10):
        """
        Reads raw data from the UART RX_FIFO.
        Parameters:
        - count (int): Number of bytes to read.
        - timeout (float): Maximum time to wait for data in seconds.
        Returns:
        - list: A list of integer values read from the RX_FIFO.
        """
        buf = []
        stop_time = time() + timeout

        while len(buf) < count and time() < stop_time:
            # Check if RX FIFO has valid data
            if self.uart.read(self.STAT_REG) & (1 << self.RX_VALID):
                # Read a single value from RX_FIFO and append to buffer
                buf.append(self.uart.read(self.RX_FIFO))

        return buf


    def write(self, data, timeout=10):
        """
        Writes a string or buffer to the UART TX_FIFO.
        Parameters:
        - data (str): The string to send over UART.
        - timeout (float): Maximum time in seconds to wait for TX_FIFO availability.
        Returns:
        - int: The number of bytes successfully written.
        """
        if not isinstance(data, str):
            raise ValueError("Data must be a string.")

        stop_time = time() + timeout
        wr_count = 0

        for char in data:
            # Wait for TX FIFO to be ready
            while time() < stop_time:
                if not (self.uart.read(self.STAT_REG) & (1 << self.TX_FULL)):
                    self.uart.write(self.TX_FIFO, ord(char))  # Write the character
                    wr_count += 1
                    break
            else:
                # Timeout occurred
                print(f"Timeout: Could not write '{char}' to TX_FIFO.")
                break

        return wr_count

    def is_data_ready(self):
        """
        Checks if the UART RX FIFO has valid data ready to be read.
        Returns:
        - bool: True if data is available in the RX FIFO, False otherwise.
        """
        return bool(self.uart.read(self.STAT_REG) & (1 << self.RX_VALID))
    