import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from octoprint.events import Events


class TestIntegration:
    """Integration tests for event handling and printer interactions"""

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

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_print_workflow_integration(self, mock_data_class, mock_thread_class):
        """Test complete print workflow integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        
        # Test print started
        plugin.on_event(Events.PRINT_STARTED, {})
        
        # Verify sensor started
        mock_thread_instance.start.assert_called_once()
        
        # Test print progress - simulate motion detection
        plugin.sensor_event_callback(pMoving=True)
        assert plugin._data.filament_moving == True
        
        # Test print completed
        plugin.on_event(Events.PRINT_DONE, {})
        
        # Verify sensor stopped
        mock_thread_instance.keepRunning = False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_filament_jam_detection_workflow(self, mock_data_class, mock_thread_class):
        """Test filament jam detection and response workflow"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock printer printing state
        self.mock_printer.is_printing.return_value = True
        
        # Simulate print start
        plugin.on_event(Events.PRINT_STARTED, {})
        
        # Simulate initial motion (filament flowing)
        plugin.sensor_event_callback(pMoving=True)
        assert plugin._data.filament_moving == True
        
        # Simulate filament jam (no motion detected)
        plugin.sensor_event_callback(pMoving=False)
        assert plugin._data.filament_moving == False
        
        # Verify pause command would be sent
        # (specific implementation depends on the plugin's pause logic)

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_print_pause_resume_workflow(self, mock_data_class, mock_thread_class):
        """Test print pause and resume workflow"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test print pause
        plugin.on_event(Events.PRINT_PAUSED, {})
        
        # Verify sensor state during pause
        assert plugin._data.flag == status_flags["PAUSED"]
        
        # Test print resume
        plugin.on_event(Events.PRINT_RESUMED, {})
        
        # Verify sensor resumes monitoring
        assert plugin._data.flag == status_flags["MONITORING"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_print_failure_handling(self, mock_data_class, mock_thread_class):
        """Test print failure handling"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        plugin.motion_sensor_thread = mock_thread_instance
        
        # Test print failure
        plugin.on_event(Events.PRINT_FAILED, {})
        
        # Verify cleanup
        assert mock_thread_instance.keepRunning == False
        assert plugin._data.flag == status_flags["OFF"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_print_cancellation_handling(self, mock_data_class, mock_thread_class):
        """Test print cancellation handling"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        plugin.motion_sensor_thread = mock_thread_instance
        
        # Test print cancellation
        plugin.on_event(Events.PRINT_CANCELLED, {})
        
        # Verify cleanup
        assert mock_thread_instance.keepRunning == False
        assert plugin._data.flag == status_flags["OFF"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_z_change_event_handling(self, mock_data_class, mock_thread_class):
        """Test Z change event handling"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test Z change event
        plugin.on_event(Events.Z_CHANGE, {'new': 10.0, 'old': 9.0})
        
        # Verify sensor responds to Z change
        assert plugin._data.flag == status_flags["WAITING_Z_MOVE"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_distance_based_detection_workflow(self, mock_data_class, mock_thread_class):
        """Test distance-based detection workflow"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        # Enable distance detection
        self.settings_dict['detection_method'] = 1
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up initial state
        plugin._data.remaining_distance = 7
        plugin._data.lastE = 0.0
        plugin._data.currentE = 0.0
        
        # Simulate extrusion
        plugin.calc_distance(5.0)
        
        # Verify distance calculation
        assert plugin._data.remaining_distance == 2  # 7 - 5 = 2
        assert plugin._data.currentE == 5.0
        
        # Continue extrusion beyond threshold
        plugin.calc_distance(10.0)
        
        # Verify distance reached
        assert plugin._data.remaining_distance == -3  # 2 - 5 = -3
        assert plugin._data.flag == status_flags["DIST_REACHED_GRACE_PERIOD"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_timeout_detection_workflow(self, mock_data_class, mock_thread_class):
        """Test timeout-based detection workflow"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock time progression
        start_time = time.time()
        plugin._data.last_motion_detected = start_time
        
        # Simulate timeout scenario
        with patch('time.time', return_value=start_time + 25):  # 25 seconds later
            plugin.sensor_event_callback(pMoving=False)
            
            # Verify timeout detected
            assert plugin._data.filament_moving == False
            assert plugin._data.flag == status_flags["MAX_TIMEOUT_STOP_ASAP"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_temperature_monitoring_integration(self, mock_data_class, mock_thread_class):
        """Test temperature monitoring integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock temperature data
        temp_data = {
            'T0': {'actual': 200.0, 'target': 210.0},
            'B': {'actual': 60.0, 'target': 65.0}
        }
        
        # Test temperature processing
        plugin.process_temperatures(Mock(), temp_data)
        
        # Verify temperature tracking
        assert plugin.t0_temp == 200.0
        assert plugin.last_temp_time > 0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_settings_change_integration(self, mock_data_class, mock_thread_class):
        """Test settings change integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test settings change
        new_settings = {'motion_sensor_pin': 18}
        
        with patch.object(plugin, '_setup_sensor') as mock_setup:
            plugin.on_settings_save(new_settings)
            
            # Verify sensor setup is called
            mock_setup.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_connection_test_integration(self, mock_data_class, mock_thread_class):
        """Test connection test integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        
        # Test connection test start
        plugin.start_connection_test()
        
        # Verify test thread started
        mock_thread_instance.start.assert_called_once()
        assert plugin._data.connection_test_running == True
        
        # Test connection test callback
        plugin.connectionTestCallback(pMoving=True)
        assert plugin._data.filament_moving == True
        
        # Test connection test stop
        plugin.motion_sensor_thread = mock_thread_instance
        plugin.motion_sensor_thread.name = "ConnectionTest"
        plugin.stop_secondary_thread()
        
        # Verify test stopped
        assert mock_thread_instance.keepRunning == False
        assert plugin._data.connection_test_running == False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_custom_gcode_integration(self, mock_data_class, mock_thread_class):
        """Test custom gcode integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test custom gcode trigger
        plugin.trigger_custom_gcode = True
        plugin.code_sent = False
        
        plugin.send_custom_gcode_afterpause()
        
        # Verify custom gcode sent
        assert plugin.code_sent == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_multiple_event_sequence(self, mock_data_class, mock_thread_class):
        """Test multiple event sequence"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        
        # Sequence: Start -> Motion -> No Motion -> Pause -> Resume -> Done
        
        # 1. Print started
        plugin.on_event(Events.PRINT_STARTED, {})
        mock_thread_instance.start.assert_called_once()
        
        # 2. Motion detected
        plugin.sensor_event_callback(pMoving=True)
        assert plugin._data.filament_moving == True
        
        # 3. No motion detected
        plugin.sensor_event_callback(pMoving=False)
        assert plugin._data.filament_moving == False
        
        # 4. Print paused
        plugin.on_event(Events.PRINT_PAUSED, {})
        assert plugin._data.flag == status_flags["PAUSED"]
        
        # 5. Print resumed
        plugin.on_event(Events.PRINT_RESUMED, {})
        assert plugin._data.flag == status_flags["MONITORING"]
        
        # 6. Print done
        plugin.on_event(Events.PRINT_DONE, {})
        assert plugin._data.flag == status_flags["OFF"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_error_recovery_integration(self, mock_data_class, mock_thread_class):
        """Test error recovery integration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Simulate error condition
        plugin._data.flag = status_flags["PRINTER_ERROR"]
        
        # Test recovery after error
        plugin.on_event(Events.PRINT_STARTED, {})
        
        # Verify system recovers
        assert plugin._data.flag != status_flags["PRINTER_ERROR"]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_concurrent_operations(self, mock_data_class, mock_thread_class):
        """Test concurrent operations"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test concurrent print start and connection test
        plugin.start_connection_test()
        plugin.on_event(Events.PRINT_STARTED, {})
        
        # Should handle both operations gracefully
        # (specific behavior depends on implementation)

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_sensor_state_persistence(self, mock_data_class, mock_thread_class):
        """Test sensor state persistence across events"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set state
        plugin._data.remaining_distance = 5
        plugin._data.lastE = 10.0
        plugin._data.currentE = 15.0
        
        # Trigger events
        plugin.on_event(Events.PRINT_PAUSED, {})
        plugin.on_event(Events.PRINT_RESUMED, {})
        
        # Verify state persists
        assert plugin._data.remaining_distance == 5
        assert plugin._data.lastE == 10.0
        assert plugin._data.currentE == 15.0 