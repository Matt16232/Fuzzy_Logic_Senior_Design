import time
import threading
from collections import deque
from ..sensors.PMOD_ACL2 import PMOD_ACL2
import math

class Velocity(PMOD_ACL2):
    def __init__(self, spi_controller, interval=0.01):
        """
        Improved velocity tracking using all axes to compensate for yaw/tilt.
        """
        super().__init__(spi_controller)
        self.interval = interval
        
        # Separate history for each axis
        self.acc_history_x = deque(maxlen=10)
        self.acc_history_y = deque(maxlen=10)
        self.acc_history_z = deque(maxlen=10)
        self.vel_history = deque(maxlen=5)
        
        # Thresholds and control values
        self.zero_threshold = 0.15
        self.yaw_threshold = 0.3  # Threshold to detect turning motion
        self.tilt_threshold = 0.2  # Threshold to detect tilting
        self.velocity = 0.0
        
        # Bias for all axes
        self.bias_x = 0.0
        self.bias_y = 0.0
        self.bias_z = 0.0
        
        # Stability controls
        self.min_stable_readings = 3
        self.stable_count = 0
        
        # Threading setup
        self._running = False
        self._lock = threading.Lock()
        self._thread = None
        self.last_update = time.time()

    def calibrate(self, samples=150):
        """
        Calibrate all axes based on actual stationary readings.
        """
        print("Calibrating - keep car still and level...")
        x_readings, y_readings, z_readings = [], [], []
        
        # Collect all readings
        for _ in range(samples):
            x_readings.append(self.read_x_acceleration())
            y_readings.append(self.read_y_acceleration())
            z_readings.append(self.read_z_acceleration())
            time.sleep(self.interval)
        
        # Calculate the actual resting values including Z
        x_readings.sort()
        y_readings.sort()
        z_readings.sort()
        
        # Use trimmed mean for each axis
        trimmed_x = x_readings[20:-20]
        trimmed_y = y_readings[20:-20]
        trimmed_z = z_readings[20:-20]
        
        # Set bias as the resting values
        self.bias_x = sum(trimmed_x) / len(trimmed_x)
        self.bias_y = sum(trimmed_y) / len(trimmed_y)
        self.bias_z = sum(trimmed_z) / len(trimmed_z)  # Use actual Z reading
        
        print(f"Calibration complete:")
        print(f"X bias: {self.bias_x:.4f}")
        print(f"Y bias: {self.bias_y:.4f}")
        print(f"Z bias: {self.bias_z:.4f}")

    def _smooth_acceleration(self, new_acc, history):
        """
        Smooth acceleration values for any axis.
        """
        history.append(new_acc)
        if len(history) < history.maxlen:
            return 0.0
        
        sorted_acc = sorted(history)
        trimmed = sorted_acc[2:-2]
        return sum(trimmed) / len(trimmed)

    def _smooth_velocity(self, new_vel):
        """
        Smooth velocity transitions using moving average.
        """
        self.vel_history.append(new_vel)
        return sum(self.vel_history) / len(self.vel_history)

    def _is_turning(self, ax, az):
        """
        Detect if car is turning based on lateral acceleration.
        """
        return abs(ax) > self.yaw_threshold

    def _is_tilted(self, az):
        """
        Detect if car is tilted based on deviation from calibrated Z value.
        """
        return abs(az - self.bias_z) > self.tilt_threshold

    def _update_velocity(self):
        """
        Update velocity considering all axes of motion.
        """
        while self._running:
            # Get acceleration for all axes
            ax = self.read_x_acceleration() - self.bias_x
            ay = self.read_y_acceleration() - self.bias_y
            az = self.read_z_acceleration() - self.bias_z
            
            # Smooth all accelerations
            smooth_ax = self._smooth_acceleration(ax, self.acc_history_x)
            smooth_ay = self._smooth_acceleration(ay, self.acc_history_y)
            smooth_az = self._smooth_acceleration(az, self.acc_history_z)
            
            with self._lock:
                # Check for turning or tilting
                turning = self._is_turning(smooth_ax, smooth_az)
                tilted = self._is_tilted(smooth_az)
                
                # Reduce acceleration effect if turning or tilted
                effective_ay = smooth_ay
                if turning:
                    effective_ay *= 0.5  # Reduce effect when turning
                if tilted:
                    effective_ay *= 0.7  # Reduce effect when tilted
                
                # Update velocity with compensation
                if abs(effective_ay) < self.zero_threshold:
                    self.stable_count = 0
                    self.velocity *= 0.95
                else:
                    self.stable_count += 1
                    if self.stable_count >= self.min_stable_readings:
                        self.velocity += effective_ay * self.interval
                
                # Apply velocity smoothing and limits
                self.velocity = self._smooth_velocity(self.velocity)
                self.velocity = max(min(self.velocity, 15.0), -15.0)
                
                if abs(self.velocity) < 0.1:
                    self.velocity = 0.0

            time.sleep(self.interval)

    def start_tracking(self):
        """Start velocity tracking with calibration."""
        if not self._running:
            self.calibrate()
            self._running = True
            self.last_update = time.time()
            self._thread = threading.Thread(target=self._update_velocity, daemon=True)
            self._thread.start()
            print("Speed tracking started")

    def stop_tracking(self):
        """Safely stop velocity tracking."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.velocity = 0.0

    def get_speed(self):
        """
        Get speed rating with hysteresis to prevent fluctuation.
        """
        with self._lock:
            speed = abs(self.velocity)
            # Add hysteresis to prevent rapid switching
            if speed < 0.3:
                return "Stopped"
            elif speed < 1.2:
                return "Slow"
            elif speed < 2.5:
                return "Medium"
            else:
                return "Fast"

    def get_direction(self):
        """
        Get direction with hysteresis to prevent rapid switching.
        """
        with self._lock:
            if abs(self.velocity) < 0.3:
                return "Stopped"
            return "Forward" if self.velocity > 0 else "Reverse"

    def get_raw_velocity(self):
        """
        Get raw velocity value for debugging.
        """
        with self._lock:
            return round(self.velocity, 3)

    def get_raw_acceleration(self):
        """
        Get current acceleration for debugging.
        """
        return round(self.read_y_acceleration() - self.bias_y, 3)

    def get_calibrated_values(self):
        """
        Get current calibrated acceleration values for all axes.
        """
        ax = self.read_x_acceleration() - self.bias_x
        ay = self.read_y_acceleration() - self.bias_y
        az = self.read_z_acceleration() - self.bias_z
        return {
            'x': round(ax, 3),
            'y': round(ay, 3),
            'z': round(az, 3)
        }