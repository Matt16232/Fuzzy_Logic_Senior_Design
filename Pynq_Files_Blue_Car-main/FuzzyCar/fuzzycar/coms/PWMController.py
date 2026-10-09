from pynq import MMIO
from time import sleep

class PWMController:
    def __init__(self, overlay, ip_name):
        self.motor = getattr(overlay, ip_name)

        ip_dict = overlay.ip_dict[ip_name]['registers']
        self.TCSR0_addr = ip_dict['TCSR0']['address_offset']
        self.TCSR1_addr = ip_dict['TCSR1']['address_offset']
        self.TLR0_addr = ip_dict['TLR0']['address_offset']
        self.TLR1_addr = ip_dict['TLR1']['address_offset']
        
        self.TCSR0_fields = ip_dict['TCSR0']['fields']
        self.TCSR1_fields = ip_dict['TCSR1']['fields']

        self.temp_val_0 = 0
        self.temp_val_1 = 0

        self._configure_pwm()

    def _set_bit(self, value, bit):
        return value | (1 << bit)

    def _clear_bit(self, value, bit):
        return value & ~(1 << bit)

    def _configure_pwm(self):
        self.temp_val_0 = self._set_bit(self.temp_val_0, self.TCSR0_fields['PWMA0']['bit_offset'])
        self.temp_val_1 = self._set_bit(self.temp_val_1, self.TCSR1_fields['PWMA1']['bit_offset'])

        self.temp_val_0 = self._set_bit(self.temp_val_0, self.TCSR0_fields['GENT0']['bit_offset'])
        self.temp_val_1 = self._set_bit(self.temp_val_1, self.TCSR1_fields['GENT1']['bit_offset'])

        self.temp_val_0 = self._set_bit(self.temp_val_0, self.TCSR0_fields['UDT0']['bit_offset'])
        self.temp_val_1 = self._set_bit(self.temp_val_1, self.TCSR1_fields['UDT1']['bit_offset'])

        self.temp_val_0 = self._set_bit(self.temp_val_0, self.TCSR0_fields['ARHT0']['bit_offset'])
        self.temp_val_1 = self._set_bit(self.temp_val_1, self.TCSR1_fields['ARHT1']['bit_offset'])

    def set_pwm_duty(self, frequency, duty_cycle):
        """Configure and start the PWM output."""
        # Check that duty_cycle is between 5 and 10
        if not (5 <= duty_cycle <= 10):
            raise ValueError("Duty cycle must be between 5 and 10 percent")

        clock_frequency = 100e6  # Adjust if the timer's clock frequency is different. Pynq Z2's Fclk0 is 100 MHz
        period = int(clock_frequency / frequency)
        pulse = int((duty_cycle / 100) * period)
        self._configure_pwm()
        # Write the period and pulse width
        self.motor.write(self.TLR0_addr, period)
        self.motor.write(self.TLR1_addr, pulse)

        # Enable the timers (ENT bits)
        self.temp_val_0 = self._set_bit(self.temp_val_0, self.TCSR0_fields['ENT0']['bit_offset'])
        self.temp_val_1 = self._set_bit(self.temp_val_1, self.TCSR1_fields['ENT1']['bit_offset'])

        # Write the control register to enable the timers
        self.motor.write(self.TCSR0_addr, self.temp_val_0)
        self.motor.write(self.TCSR1_addr, self.temp_val_1)

    def set_pwm_time(self, frequency, pulse_width_us):
        """Configure and start the PWM output with pulse width specified in microseconds."""
        # Check that the pulse width is between 1100 and 1700 microseconds.

        clock_frequency = 100e6  # Timer's clock frequency (e.g., 100 MHz for Pynq Z2's Fclk0)
        period = int(clock_frequency / frequency)

        # Convert pulse width from microseconds to timer counts.
        pulse = int((pulse_width_us * clock_frequency) / 1e6)

        self._configure_pwm()

        # Write the period and pulse width.
        self.motor.write(self.TLR0_addr, period)
        self.motor.write(self.TLR1_addr, pulse)

        # Enable the timers (set the ENT bits).
        self.temp_val_0 = self._set_bit(self.temp_val_0, self.TCSR0_fields['ENT0']['bit_offset'])
        self.temp_val_1 = self._set_bit(self.temp_val_1, self.TCSR1_fields['ENT1']['bit_offset'])

        # Write the control registers to start the timers.
        self.motor.write(self.TCSR0_addr, self.temp_val_0)
        self.motor.write(self.TCSR1_addr, self.temp_val_1)

    def stop(self):
        """Stop the PWM output and ensure it stops in the low state."""
        # Step 1: Clear PWM mode to prevent toggling
        self.temp_val_0 = self._clear_bit(self.temp_val_0, self.TCSR0_fields['PWMA0']['bit_offset'])
        self.temp_val_1 = self._clear_bit(self.temp_val_1, self.TCSR1_fields['PWMA1']['bit_offset'])

        # Step 2: Clear GenerateOut signals to disable output toggling
        self.temp_val_0 = self._clear_bit(self.temp_val_0, self.TCSR0_fields['GENT0']['bit_offset'])
        self.temp_val_1 = self._clear_bit(self.temp_val_1, self.TCSR1_fields['GENT1']['bit_offset'])

        # Step 3: Set the pulse width to 0 (force low output)
        self.motor.write(self.TLR1_addr, 0)

        # Step 4: Set a minimal period value to stabilize the timer (if required by hardware)
        self.motor.write(self.TLR0_addr, 1)  # Set period to a small non-zero value

        # Step 5: Disable the timers (halt counters)
        self.temp_val_0 = self._clear_bit(self.temp_val_0, self.TCSR0_fields['ENT0']['bit_offset'])
        self.temp_val_1 = self._clear_bit(self.temp_val_1, self.TCSR1_fields['ENT1']['bit_offset'])

        # Step 6: Write the final values to the control registers
        self.motor.write(self.TCSR0_addr, self.temp_val_0)
        self.motor.write(self.TCSR1_addr, self.temp_val_1)

