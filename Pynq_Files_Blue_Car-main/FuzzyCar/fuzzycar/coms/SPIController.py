from pynq import MMIO

class SPIController:
    # SPI Register Offsets
    RESET_REG = 0x40
    CONTROL_REG = 0x60
    STATUS_REG = 0x64
    DATA_TO_SEND = 0x68
    DATA_RECEIVED = 0x6C
    SLAVE_SELECT = 0x70
    SEND_QUEUE_STATUS = 0x74
    RECEIVE_QUEUE_STATUS = 0x78
    GLOBAL_INT_ENABLE = 0x1C
    INTERRUPT_STATUS = 0x20
    INTERRUPT_ENABLE = 0x28

    # Bit Masks
    RESET_MASK = 0x0A
    TX_EMPTY_FLAG = 0x04
    TX_FULL_FLAG = 0x08
    STOP_TRANSMIT_MASK = 0x100
    LOOPBACK_MODE = 0x01
    ENABLE_SPI = 0x02
    MASTER_MODE = 0x04
    CLOCK_POLARITY = 0x08
    CLOCK_PHASE = 0x10
    RESET_TX_QUEUE = 0x20
    RESET_RX_QUEUE = 0x40
    MANUAL_SLAVE_SELECT = 0x80

    # Miscellaneous Constants
    NO_SLAVE_SELECTED = 0xFFFFFFFF

    def __init__(self, address):
        self.spi = MMIO(address, 0x10000, debug=False)  # Store the SPI hardware instance
        self.address = address
    
        

    def configure(self, clock_phase=0, clock_polarity=0, is_master=True):
        print("Configuring SPI controller...")
        # Reset the SPI controller
        self.spi.write(self.RESET_REG, self.RESET_MASK)

        # Disable global interrupts and deselect slaves
        self.spi.write(self.GLOBAL_INT_ENABLE, 0)
        self.spi.write(self.SLAVE_SELECT, self.NO_SLAVE_SELECTED)

        # Read the control register and configure settings
        control_settings = self.spi.read(self.CONTROL_REG)
        if is_master:
            control_settings |= self.MASTER_MODE
        control_settings |= self.ENABLE_SPI | self.RESET_TX_QUEUE | self.RESET_RX_QUEUE | self.MANUAL_SLAVE_SELECT
        self.spi.write(self.CONTROL_REG, control_settings)

        # Adjust clock settings
        control_settings = self.spi.read(self.CONTROL_REG)
        control_settings &= ~(self.CLOCK_PHASE | self.CLOCK_POLARITY)
        if clock_phase == 1:
            control_settings |= self.CLOCK_PHASE
        if clock_polarity == 1:
            control_settings |= self.CLOCK_POLARITY
        self.spi.write(self.CONTROL_REG, control_settings)

    def transfer(self, data_packet):
        responses = []

        for data in data_packet:
            # Write data to the transmit register
            self.spi.write(self.DATA_TO_SEND, data)
            self.spi.write(self.SLAVE_SELECT, 0xFFFFFFFE)

            # Start transmission
            control_settings = self.spi.read(self.CONTROL_REG)
            control_settings &= ~self.STOP_TRANSMIT_MASK
            self.spi.write(self.CONTROL_REG, control_settings)

            # Wait for transmission to complete
            status = self.spi.read(self.STATUS_REG)
            while not (status & self.TX_EMPTY_FLAG):
                status = self.spi.read(self.STATUS_REG)

            # Read received data
            responses.append(self.spi.read(self.DATA_RECEIVED))


            # End transmission
            control_settings = self.spi.read(self.CONTROL_REG)
            control_settings |= self.STOP_TRANSMIT_MASK
            self.spi.write(self.CONTROL_REG, control_settings)

        # Deselect the slave device
        self.spi.write(self.SLAVE_SELECT, self.NO_SLAVE_SELECTED)
        return responses
    
    def send(self, data_packet):
        for data in data_packet:
            self.spi.write(self.DATA_TO_SEND, data)
            self.spi.write(self.SLAVE_SELECT, 0xFFFFFFFE)

            # Start transmission
            control_settings = self.spi.read(self.CONTROL_REG)
            control_settings &= ~self.STOP_TRANSMIT_MASK
            self.spi.write(self.CONTROL_REG, control_settings)

            # Wait for transmission to complete
            status = self.spi.read(self.STATUS_REG)
            while not (status & self.TX_EMPTY_FLAG):
                status = self.spi.read(self.STATUS_REG)
            # End transmission
            control_settings = self.spi.read(self.CONTROL_REG)
            control_settings |= self.STOP_TRANSMIT_MASK
            self.spi.write(self.CONTROL_REG, control_settings)

        # Deselect the slave device
        self.spi.write(self.SLAVE_SELECT, self.NO_SLAVE_SELECTED)
        return 0 