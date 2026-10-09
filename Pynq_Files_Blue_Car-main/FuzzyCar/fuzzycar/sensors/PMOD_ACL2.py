import time
class PMOD_ACL2:
    # PMOD ACL2 Register Addresses
    SOFT_RESET_REG = 0x1F
    POWER_CTL_REG = 0x2D
    DEVICE_ID_REG = 0x00
    XDATA_L_REG = 0x0E  # X-axis acceleration data (low byte)
    XDATA_H_REG = 0x0F  # X-axis acceleration data (high byte)
    YDATA_L_REG = 0x10  # Y-axis acceleration data (low byte)
    YDATA_H_REG = 0x11  # Y-axis acceleration data (high byte)
    ZDATA_L_REG = 0x12  # Z-axis acceleration data (low byte)
    ZDATA_H_REG = 0x13  # Z-axis acceleration data (high byte)

    # Expected Device ID
    DEVICE_ID_EXPECTED = 0xAD

    # Sensitivity for ±2g range (1 LSB = 1 mg = 0.00980665 m/s²)
    SENSITIVITY = 0.00980665  # m/s² per LSB

    def __init__(self, spi_controller):
        """
        Initialize the PMOD_ACL2 object with the SPI controller.
        """
        self.spi_controller = spi_controller
        self.bias_x = 0.0
        self.bias_y = 0.0
        self.bias_z = 0.0

    def initialize(self):
        """
        Perform the initialization sequence for the PMOD ACL2.
        """
        print("Initializing PMOD ACL2...")

        # Reset the device
        self.write_register(self.SOFT_RESET_REG, 0x52)  # Soft reset

        # Enable measurement mode
        self.enable_measurement_mode()

        # Verify device ID
        device_id = self.read_register(self.DEVICE_ID_REG)
        print(f"Device ID: 0x{device_id:02X}")
        if device_id != self.DEVICE_ID_EXPECTED:
            raise ValueError(f"Initialization Failed: Expected 0x{self.DEVICE_ID_EXPECTED:02X}, Got 0x{device_id:02X}")
        print("PMOD ACL2 successfully initialized.")

    def enable_measurement_mode(self):
        """
        Ensure the PMOD ACL2 is in measurement mode.
        """
        current_mode = self.read_register(self.POWER_CTL_REG)
        if current_mode != 0x02:
            print("Enabling measurement mode...")
            self.write_register(self.POWER_CTL_REG, 0x02)

    def write_register(self, reg_address, value):
        """
        Write a value to a specific register.
        """
        packet = [0x0A, reg_address, value]
        self.spi_controller.transfer(packet)

    def read_register(self, reg_address):
        """
        Read a value from a specific register.
        """
        packet = [0x0B, reg_address]  # Read command with dummy byte
        response = self.spi_controller.transfer(packet)
        return response[-1]

    def _convert_to_m_s2(self, raw_value):
        """
        Convert raw accelerometer data to meters per second squared (m/s²).
        :param raw_value: Raw accelerometer value (2's complement).
        :return: Acceleration in m/s².
        """
        # Convert from two's complement if the value is negative
        if raw_value & 0x800:  # Check if the 12th bit (sign bit) is set
            raw_value -= 1 << 12  # Convert to signed 12-bit value

        # Scale the value to m/s²
        return raw_value * self.SENSITIVITY

    def _read_raw_acceleration(self, low_reg, high_reg):
        """
        Read raw 12-bit acceleration data from the given low and high byte registers.
        :param low_reg: Register address for the low byte.
        :param high_reg: Register address for the high byte.
        :return: 12-bit raw acceleration data.
        """
        low_byte = self.read_register(low_reg)
        high_byte = self.read_register(high_reg)

        # Combine high and low bytes into a 12-bit value
        raw_value = (high_byte << 8) | low_byte

        # Mask out extra bits (12-bit data)
        raw_value &= 0xFFF

        return raw_value

    def read_x_acceleration(self):
        """
        Read the X-axis acceleration in m/s².
        """
        raw_x = self._read_raw_acceleration(self.XDATA_L_REG, self.XDATA_H_REG)
        return self._convert_to_m_s2(raw_x) - self.bias_x

    def read_y_acceleration(self):
        """
        Read the Y-axis acceleration in m/s².
        """
        raw_y = self._read_raw_acceleration(self.YDATA_L_REG, self.YDATA_H_REG)
        return self._convert_to_m_s2(raw_y) - self.bias_y

    def read_z_acceleration(self):
        """
        Read the Z-axis acceleration in m/s².
        """
        raw_z = self._read_raw_acceleration(self.ZDATA_L_REG, self.ZDATA_H_REG)
        return self._convert_to_m_s2(raw_z) - self.bias_z

    def calibrate(self, samples=200, interval=0.01):
        """
        Calibrate the accelerometer to remove bias by averaging stationary readings.
        """
        print("Calibrating... Please keep the device still.")
        x_readings = []
        y_readings = []
        z_readings = []

        for _ in range(samples):
            x_readings.append(self.read_x_acceleration() + self.bias_x)  # Undo current bias during reading
            y_readings.append(self.read_y_acceleration() + self.bias_y)
            z_readings.append(self.read_z_acceleration() + self.bias_z)
            time.sleep(interval)

        # Compute average biases
        self.bias_x = sum(x_readings) / samples
        self.bias_y = sum(y_readings) / samples
        self.bias_z = sum(z_readings) / samples

        print(f"Calibration complete: Bias X={self.bias_x:.4f}, Y={self.bias_y:.4f}, Z={self.bias_z:.4f}")
