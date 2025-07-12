import pytest
import time
from unittest.mock import Mock, patch, MagicMock


class TestSensorLogic:
    """Test suite for sensor logic and status flags"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()
        self.mock_printer = Mock()
        self.mock_settings = Mock()
        
        # Set up settings defaults
        self.settings_dict = {
            'mode': 0,
            'motion_sensor_enabled': True,
            'motion_sensor_pin': 17,
            'detection_method': 0,
            'motion_sensor_detection_distance': 7,
            'motion_sensor_max_not_moving': 20,
            'motion_sensor_max_not_moving_after_dist': 10,
            'initial_delay': 60,
            'heaters_timeout': 20,
            'pause_command': '@pause',
            'motion_sensor_pause_print': True
        }
        
        self.mock_settings.get.side_effect = lambda keys: self.settings_dict.get(keys[0])
        self.mock_settings.get_boolean.side_effect = lambda keys: self.settings_dict.get(keys[0])

    def test_status_flags_constants(self):
        """Test that all status flags are defined correctly"""
        from octoprint_filamentmotionsensor import status_flags
        
        expected_flags = {
            "PRINTER_ERROR": -10,
            "PAUSED_HEATERS_OFF": -6,
            "PAUSED_HEATERS_UNSURE": -5,
            "PAUSED_EXTRINSIC": -4,
            "PAUSED_ON_RESUME_T0_LOW": -3,
            "PAUSED_JAMMED": -2,
            "OFF": -1,
            "PAUSED": 0,
            "WAITING_Z_MOVE": 4,
            "WAITING_E_MOVE": 6,
            "WAITING_START_DELAY": 9,
            "MONITORING": 10,
            "ANTICIPATING_JAM": 11,
            "TIMEOUT_10S_LEFT": 12,
            "DIST_REACHED_GRACE_PERIOD": 20,
            "TIMEOUT_10S_LEFT_DIST_REACHED": 22,
            "DIST_REACHED_STOP_ASAP": 25,
            "MAX_TIMEOUT_STOP_ASAP": 26,
            "JAMMED_AWAITING_MOTION": 30,
        }
        
        for flag_name, expected_value in expected_flags.items():
            assert status_flags[flag_name] == expected_value

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_distance_calculation_basic(self, mock_data_class, mock_thread_class):
        """Test basic distance calculation"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up initial state
        plugin._data.lastE = 5.0
        plugin._data.currentE = 5.0
        plugin._data.remaining_distance = 7
        
        # Test distance calculation with new extrusion
        plugin.calc_distance(10.0)
        
        # Verify calculation: 7 - (10 - 5) = 2
        assert plugin._data.currentE == 10.0
        assert plugin._data.remaining_distance == 2
        assert plugin._data.lastE == 5.0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_distance_calculation_negative_remaining(self, mock_data_class, mock_thread_class):
        """Test distance calculation when remaining distance goes negative"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up initial state
        plugin._data.lastE = 5.0
        plugin._data.currentE = 5.0
        plugin._data.remaining_distance = 3
        
        # Test distance calculation with large extrusion
        plugin.calc_distance(15.0)
        
        # Verify calculation: 3 - (15 - 5) = -7
        assert plugin._data.currentE == 15.0
        assert plugin._data.remaining_distance == -7
        assert plugin._data.lastE == 5.0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_distance_calculation_no_extrusion(self, mock_data_class, mock_thread_class):
        """Test distance calculation with no extrusion change"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up initial state
        plugin._data.lastE = 5.0
        plugin._data.currentE = 5.0
        plugin._data.remaining_distance = 7
        
        # Test distance calculation with same extrusion
        plugin.calc_distance(5.0)
        
        # Verify no change: 7 - (5 - 5) = 7
        assert plugin._data.currentE == 5.0
        assert plugin._data.remaining_distance == 7
        assert plugin._data.lastE == 5.0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_distance_calculation_retraction(self, mock_data_class, mock_thread_class):
        """Test distance calculation with retraction (negative extrusion)"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up initial state
        plugin._data.lastE = 10.0
        plugin._data.currentE = 10.0
        plugin._data.remaining_distance = 7
        
        # Test distance calculation with retraction
        plugin.calc_distance(5.0)
        
        # Verify calculation: 7 - (5 - 10) = 7 - (-5) = 12
        assert plugin._data.currentE == 5.0
        assert plugin._data.remaining_distance == 12
        assert plugin._data.lastE == 10.0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_reset_distance_functionality(self, mock_data_class, mock_thread_class):
        """Test distance reset functionality"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up non-default state
        plugin._data.remaining_distance = 15
        
        # Reset distance
        plugin.reset_distance()
        
        # Verify reset to default
        assert plugin._data.remaining_distance == 7  # motion_sensor_detection_distance

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_init_distance_detection(self, mock_data_class, mock_thread_class):
        """Test distance detection initialization"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up test state
        plugin._data.lastE = 5.0
        plugin._data.currentE = 10.0
        
        # Initialize distance detection
        plugin.init_distance_detection()
        
        # Verify initialization
        assert plugin._data.lastE == 10.0  # currentE should be copied to lastE

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_reset_remaining_distance(self, mock_data_class, mock_thread_class):
        """Test remaining distance reset"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up test state
        plugin._data.remaining_distance = 15
        
        # Reset remaining distance
        plugin.reset_remainin_distance()
        
        # Verify reset
        assert plugin._data.remaining_distance == 7  # motion_sensor_detection_distance

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_sensor_event_callback_with_flag_updates(self, mock_data_class, mock_thread_class):
        """Test sensor event callback with status flag updates"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test motion detected
        plugin.sensor_event_callback(pMoving=True)
        
        assert plugin._data.filament_moving == True
        assert plugin._data.flag == status_flags["MONITORING"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_sensor_event_callback_no_motion_timeout(self, mock_data_class, mock_thread_class):
        """Test sensor event callback when no motion detected and timeout occurs"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock printer state
        self.mock_printer.is_printing.return_value = True
        
        # Test no motion detected
        plugin.sensor_event_callback(pMoving=False)
        
        assert plugin._data.filament_moving == False
        # Flag should indicate some form of timeout or jam detection

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_connection_test_callback(self, mock_data_class, mock_thread_class):
        """Test connection test callback"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test connection test with motion
        plugin.connectionTestCallback(pMoving=True)
        
        assert plugin._data.filament_moving == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_main_thread_cleanup(self, mock_data_class, mock_thread_class):
        """Test main thread cleanup functionality"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up thread
        mock_thread_instance = Mock()
        plugin.motion_sensor_thread = mock_thread_instance
        
        # Test cleanup
        plugin.main_thread_cleanup("test_event")
        
        # Verify cleanup
        assert mock_thread_instance.keepRunning == False
        assert plugin.motion_sensor_thread is None
        assert plugin._data.flag == status_flags["OFF"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_distance_hook_integration(self, mock_data_class, mock_thread_class):
        """Test distance detection hook integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up for distance detection mode
        self.settings_dict['detection_method'] = 1
        plugin.hook_it = True
        
        # Mock comm and gcode
        mock_comm = Mock()
        mock_gcode = Mock()
        mock_gcode.get_float.return_value = 15.0
        
        # Test distance detection hook
        result = plugin.distance_detection(mock_comm, "sending", "G1 E15.0", "cmd", mock_gcode)
        
        # Verify hook executed
        assert result is None  # Hook should not interfere with command

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_temperature_processing(self, mock_data_class, mock_thread_class):
        """Test temperature processing for heater timeout detection"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock temperature data
        mock_temps = {
            'T0': {'actual': 200.0, 'target': 210.0},
            'B': {'actual': 60.0, 'target': 65.0}
        }
        
        # Test temperature processing
        plugin.process_temperatures(Mock(), mock_temps)
        
        # Verify temperature is tracked
        assert plugin.t0_temp == 200.0
        assert plugin.last_temp_time > 0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_custom_gcode_trigger(self, mock_data_class, mock_thread_class):
        """Test custom gcode triggering"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up for custom gcode
        plugin.trigger_custom_gcode = True
        plugin.code_sent = False
        
        # Test custom gcode sending
        plugin.send_custom_gcode_afterpause()
        
        # Verify state change
        assert plugin.code_sent == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_custom_gcode_test(self, mock_data_class, mock_thread_class):
        """Test custom gcode validation"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test valid gcode
        test_gcode = ["G1 X10", "G1 Y10", "M117 Test"]
        result = plugin.test_custom_gcode_commands(test_gcode)
        
        # Should not raise an exception
        assert result is None

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_update_hook_control(self, mock_data_class, mock_thread_class):
        """Test hook update control"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test hook enable
        plugin.hook_it = False
        plugin.update_hook()
        
        # Verify hook is updated (specific behavior depends on implementation)
        # This test verifies the method can be called without errors

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_detection_method_switching(self, mock_data_class, mock_thread_class):
        """Test switching between detection methods"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test timeout detection (method 0)
        self.settings_dict['detection_method'] = 0
        assert plugin.detection_method == 0
        
        # Test distance detection (method 1)
        self.settings_dict['detection_method'] = 1
        assert plugin.detection_method == 1

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_pause_command_configuration(self, mock_data_class, mock_thread_class):
        """Test pause command configuration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test default pause command
        assert plugin.pause_command == '@pause'
        
        # Test custom pause command
        self.settings_dict['pause_command'] = 'M600'
        assert plugin.pause_command == 'M600'

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_sensor_pin_validation(self, mock_data_class, mock_thread_class):
        """Test sensor pin validation"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test valid pin
        self.settings_dict['motion_sensor_pin'] = 17
        assert plugin.motion_sensor_pin == 17
        
        # Test invalid pin
        self.settings_dict['motion_sensor_pin'] = -1
        assert plugin.motion_sensor_pin == -1 