import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import flask


class TestApiCommands:
    """Test suite for API command handling"""

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
    def test_get_api_commands_structure(self, mock_data_class, mock_thread_class):
        """Test API commands structure"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        commands = plugin.get_api_commands()
        
        # Check all expected commands are present
        expected_commands = [
            'testSensor', 'stopConnectionTest', 'getSensorData', 
            'sendTestGcode', 'testCustomGcode'
        ]
        
        for cmd in expected_commands:
            assert cmd in commands
            
        # Check command structure
        assert isinstance(commands, dict)
        for cmd_name, cmd_config in commands.items():
            if cmd_name in ['testSensor', 'stopConnectionTest', 'getSensorData']:
                # These commands should have no parameters
                assert cmd_config == []
            elif cmd_name in ['sendTestGcode', 'testCustomGcode']:
                # These commands should have gcode parameter
                assert 'gcode' in [param for param in cmd_config if isinstance(param, dict)]

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_get_sensor_data(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test getSensorData API command"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock jsonify response
        expected_response = {
            'sensor_enabled': True,
            'sensor_pin': 17,
            'detection_method': 0,
            'filament_moving': False,
            'remaining_distance': 7,
            'flag': -1
        }
        mock_jsonify.return_value = expected_response
        
        # Test command
        result = plugin.on_api_command('getSensorData', {})
        
        # Verify response
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_test_sensor(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test testSensor API command"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock jsonify response
        expected_response = {'status': 'connection_test_started'}
        mock_jsonify.return_value = expected_response
        
        # Test command
        with patch.object(plugin, 'start_connection_test') as mock_start_test:
            result = plugin.on_api_command('testSensor', {})
            
            # Verify test started
            mock_start_test.assert_called_once()
            mock_jsonify.assert_called_once()
            assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_stop_connection_test(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test stopConnectionTest API command"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock jsonify response
        expected_response = {'status': 'connection_test_stopped'}
        mock_jsonify.return_value = expected_response
        
        # Test command
        with patch.object(plugin, 'stop_secondary_thread') as mock_stop_test:
            result = plugin.on_api_command('stopConnectionTest', {})
            
            # Verify test stopped
            mock_stop_test.assert_called_once()
            mock_jsonify.assert_called_once()
            assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_send_test_gcode(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test sendTestGcode API command"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock jsonify response
        expected_response = {'status': 'gcode_sent'}
        mock_jsonify.return_value = expected_response
        
        # Test command with gcode
        test_data = {'gcode': 'G1 X10 Y10'}
        result = plugin.on_api_command('sendTestGcode', test_data)
        
        # Verify gcode was processed
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_test_custom_gcode(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test testCustomGcode API command"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock jsonify response
        expected_response = {'status': 'gcode_tested', 'valid': True}
        mock_jsonify.return_value = expected_response
        
        # Test command with valid gcode
        test_data = {'gcode': 'G1 X10\nG1 Y10\nM117 Test'}
        
        with patch.object(plugin, 'test_custom_gcode_commands') as mock_test_gcode:
            mock_test_gcode.return_value = None  # No exception means valid
            result = plugin.on_api_command('testCustomGcode', test_data)
            
            # Verify gcode was tested
            mock_test_gcode.assert_called_once()
            mock_jsonify.assert_called_once()
            assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_invalid_command(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test invalid API command"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Test invalid command
        result = plugin.on_api_command('invalidCommand', {})
        
        # Should return None or handle gracefully
        assert result is None

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_missing_data(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test API command with missing data"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock jsonify response for error
        expected_response = {'status': 'error', 'message': 'missing_gcode'}
        mock_jsonify.return_value = expected_response
        
        # Test command with missing gcode parameter
        result = plugin.on_api_command('sendTestGcode', {})
        
        # Should handle missing data gracefully
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_get_sensor_data_detailed(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test getSensorData with detailed sensor state"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up detailed sensor state
        plugin._data.flag = status_flags["MONITORING"]
        plugin._data.filament_moving = True
        plugin._data.remaining_distance = 3
        plugin._data.connection_test_running = False
        
        # Mock detailed response
        expected_response = {
            'sensor_enabled': True,
            'sensor_pin': 17,
            'detection_method': 0,
            'filament_moving': True,
            'remaining_distance': 3,
            'flag': status_flags["MONITORING"],
            'connection_test_running': False,
            'max_not_moving': 20,
            'max_not_moving_after_dist': 10,
            'initial_delay': 60,
            'heaters_timeout': 20
        }
        mock_jsonify.return_value = expected_response
        
        # Test command
        result = plugin.on_api_command('getSensorData', {})
        
        # Verify detailed response
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_test_sensor_when_disabled(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test testSensor when sensor is disabled"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        # Disable sensor
        self.settings_dict['motion_sensor_enabled'] = False
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock error response
        expected_response = {'status': 'error', 'message': 'sensor_disabled'}
        mock_jsonify.return_value = expected_response
        
        # Test command
        result = plugin.on_api_command('testSensor', {})
        
        # Should return error status
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_test_sensor_invalid_pin(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test testSensor with invalid pin"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        # Set invalid pin
        self.settings_dict['motion_sensor_pin'] = -1
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock error response
        expected_response = {'status': 'error', 'message': 'invalid_pin'}
        mock_jsonify.return_value = expected_response
        
        # Test command
        result = plugin.on_api_command('testSensor', {})
        
        # Should return error status
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_custom_gcode_validation_error(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test testCustomGcode with validation error"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock validation error response
        expected_response = {'status': 'error', 'message': 'invalid_gcode', 'valid': False}
        mock_jsonify.return_value = expected_response
        
        # Test command with invalid gcode
        test_data = {'gcode': 'INVALID_GCODE'}
        
        with patch.object(plugin, 'test_custom_gcode_commands') as mock_test_gcode:
            mock_test_gcode.side_effect = Exception("Invalid gcode")
            result = plugin.on_api_command('testCustomGcode', test_data)
            
            # Verify error handling
            mock_test_gcode.assert_called_once()
            mock_jsonify.assert_called_once()
            assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    @patch('flask.request')
    def test_api_command_with_flask_request(self, mock_request, mock_jsonify, mock_data_class, mock_thread_class):
        """Test API command with Flask request context"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock Flask request
        mock_request.json = {'gcode': 'G1 X10 Y10'}
        
        # Mock jsonify response
        expected_response = {'status': 'gcode_sent'}
        mock_jsonify.return_value = expected_response
        
        # Test command
        result = plugin.on_api_command('sendTestGcode', mock_request.json)
        
        # Verify request was processed
        mock_jsonify.assert_called_once()
        assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_api_command_concurrent_test_requests(self, mock_data_class, mock_thread_class):
        """Test handling concurrent test requests"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up existing connection test
        plugin._data.connection_test_running = True
        
        with patch.object(plugin, 'start_connection_test') as mock_start_test:
            with patch('flask.jsonify') as mock_jsonify:
                # Mock response for already running test
                expected_response = {'status': 'test_already_running'}
                mock_jsonify.return_value = expected_response
                
                # Try to start another test
                result = plugin.on_api_command('testSensor', {})
                
                # Should not start new test
                mock_start_test.assert_not_called()
                mock_jsonify.assert_called_once()
                assert result == expected_response

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_api_command_sensor_data_during_print(self, mock_jsonify, mock_data_class, mock_thread_class):
        """Test getSensorData during active print"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor, status_flags
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Mock printer printing state
        self.mock_printer.is_printing.return_value = True
        plugin._data.flag = status_flags["MONITORING"]
        plugin._data.filament_moving = True
        
        # Mock response during print
        expected_response = {
            'sensor_enabled': True,
            'sensor_pin': 17,
            'detection_method': 0,
            'filament_moving': True,
            'remaining_distance': 7,
            'flag': status_flags["MONITORING"],
            'printer_printing': True
        }
        mock_jsonify.return_value = expected_response
        
        # Test command
        result = plugin.on_api_command('getSensorData', {})
        
        # Verify print state is included
        mock_jsonify.assert_called_once()
        assert result == expected_response 