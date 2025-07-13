import threading
import time

try:
    from PyMCP2221A import PyMCP2221A
except Exception:  # pragma: no cover - optional dependency
    PyMCP2221A = None


# Helper used by __plugin_check__ to verify the MCP2221A dependency

def plugin_check_mcp2221():
    """Return True if the PyMCP2221A library is available."""
    return PyMCP2221A is not None


class MotionSensorMCP2221Thread(threading.Thread):
    """Monitor the motion sensor pin using an MCP2221A device."""

    def __init__(self, threadID, threadName, pUsedPin, pMaxNotMovingTime, pLogger, pData, pCallback=None):
        super().__init__()
        self.threadID = threadID
        self.name = threadName
        self.callback = pCallback
        self._logger = pLogger
        self._data = pData
        self.used_pin = pUsedPin
        self.max_not_moving_time = pMaxNotMovingTime
        self.keepRunning = True
        self.device = None

    def run(self):
        if PyMCP2221A is None:
            self._logger.error("PyMCP2221A library not available")
            return
        try:
            self.device = PyMCP2221A.PyMCP2221A()
            self.device.DetectDevice()
            self.device.GPIO_Init()
            # configure pin as input
            self.device.GPIO_SetDirection(self.used_pin, 0)
        except Exception as ex:  # pragma: no cover - hardware dependant
            self._logger.error("Unable to initialise MCP2221", exc_info=ex)
            return

        last_val = self.device.GPIO_Read(self.used_pin)
        self._data.last_motion_detected = time.time()

        while self.keepRunning:
            try:
                val = self.device.GPIO_Read(self.used_pin)
            except Exception as ex:  # pragma: no cover - hardware dependant
                self._logger.error("Failed reading MCP2221", exc_info=ex)
                break
            if val != last_val:
                last_val = val
                self._data.last_motion_detected = time.time()
                if self.callback:
                    self.callback(bool(val))
            if time.time() - self._data.last_motion_detected > self.max_not_moving_time:
                if self.callback:
                    self.callback(False)
            time.sleep(0.01)
