import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
import octoprint.plugin
from octoprint.events import Events


class TestFilamentMotionSensorPlugin:
    """Test suite for FilamentMotionSensor plugin main class"""

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
    def test_initialization(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test plugin initialization"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        
        plugin.initialize()
        
        # Check initialization values
        assert plugin.lastE == -1
        assert plugin.currentE == -1
        assert plugin.START_DISTANCE_OFFSET == 7
        assert plugin.print_start_time == 0
        assert plugin.print_pause_time == 0
        assert plugin.last_pause_t0 == -255
        assert plugin.code_sent == False
        assert plugin.trigger_custom_gcode == False
        assert plugin.t0_temp == -255
        assert plugin.hook_it == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_property_accessors(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test property accessors"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._settings = self.mock_settings
        
        # Test all properties
        assert plugin.motion_sensor_pin == 17
        assert plugin.motion_sensor_pause_print == True
        assert plugin.detection_method == 0
        assert plugin.motion_sensor_enabled == True
        assert plugin.pause_command == '@pause'
        assert plugin.motion_sensor_detection_distance == 7
        assert plugin.motion_sensor_max_not_moving == 20
        assert plugin.motion_sensor_max_not_moving_after_dist == 10
        assert plugin.initial_delay == 60
        assert plugin.heaters_timeout == 20
        assert plugin.mode == 0

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_get_settings_defaults(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test default settings"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        defaults = plugin.get_settings_defaults()
        
        expected_defaults = {
            'mode': 0,
            'motion_sensor_enabled': True,
            'motion_sensor_pin': -1,
            'detection_method': 0,
            'motion_sensor_detection_distance': 7,
            'motion_sensor_max_not_moving': 20,
            'motion_sensor_max_not_moving_after_dist': 10,
            'initial_delay': 60,
            'heaters_timeout': 20,
            'pause_command': '@pause',
        }
        
        for key, value in expected_defaults.items():
            assert defaults[key] == value

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_setup_sensor_enabled(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test sensor setup when enabled"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin._setup_sensor()
        
        self.mock_logger.info.assert_called_with("Using BCM Mode ONLY")
        assert plugin.motion_sensor_thread is None
        assert plugin._data.filament_moving == False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_setup_sensor_disabled(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test sensor setup when disabled"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        self.settings_dict['motion_sensor_enabled'] = False
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin._setup_sensor()
        
        self.mock_logger.info.assert_any_call("Motion sensor is deactivated")

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_motion_sensor_start_enabled(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test starting motion sensor when enabled"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        
        plugin.motion_sensor_start()
        
        # Verify thread creation and start
        mock_thread_class.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify logging
        self.mock_logger.info.assert_any_call("Motion sensor started. dist:7 time:" + str(plugin._data.last_motion_detected))

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_motion_sensor_start_disabled(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test starting motion sensor when disabled"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        self.settings_dict['motion_sensor_enabled'] = False
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin.motion_sensor_start()
        
        # Verify thread is not created
        mock_thread_class.assert_not_called()
        assert plugin.motion_sensor_enabled == False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_motion_sensor_start_invalid_pin(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test starting motion sensor with invalid pin"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        self.settings_dict['motion_sensor_pin'] = -1
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin.motion_sensor_start()
        
        # Verify thread is not created
        mock_thread_class.assert_not_called()
        assert plugin.motion_sensor_enabled == False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_motion_sensor_stop_thread(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test stopping motion sensor thread"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_instance.keepRunning = True
        plugin.motion_sensor_thread = mock_thread_instance
        
        plugin.motion_sensor_stop_thread()
        
        # Verify thread is stopped
        assert mock_thread_instance.keepRunning == False
        assert plugin.motion_sensor_thread is None

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_sensor_event_callback_motion_detected(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test sensor event callback when motion is detected"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin.sensor_event_callback(pMoving=True)
        
        # Verify data is updated
        assert plugin._data.filament_moving == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_sensor_event_callback_no_motion(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test sensor event callback when no motion is detected"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin.sensor_event_callback(pMoving=False)
        
        # Verify data is updated
        assert plugin._data.filament_moving == False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_reset_distance(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test distance reset functionality"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        plugin.reset_distance()
        
        # Verify distance is reset
        assert plugin._data.remaining_distance == 7  # detection_distance

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_calc_distance(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test distance calculation"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        # Set up test data
        plugin._data.lastE = 5.0
        plugin._data.currentE = 10.0
        plugin._data.remaining_distance = 7
        
        plugin.calc_distance(15.0)
        
        # Verify distance calculation
        assert plugin._data.currentE == 15.0
        assert plugin._data.remaining_distance == 2  # 7 - (15-10) = 2

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_connection_test_start(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test starting connection test"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance
        
        plugin.start_connection_test()
        
        # Verify connection test thread is created and started
        mock_thread_class.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        assert plugin._data.connection_test_running == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_connection_test_stop(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test stopping connection test"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_thread_instance = Mock()
        mock_thread_instance.name = "ConnectionTest"
        mock_thread_instance.keepRunning = True
        plugin.motion_sensor_thread = mock_thread_instance
        
        plugin.stop_secondary_thread()
        
        # Verify connection test is stopped
        assert mock_thread_instance.keepRunning == False
        assert plugin.motion_sensor_thread is None
        assert plugin._data.connection_test_running == False

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_on_event_print_started(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test event handling for print started"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        with patch.object(plugin, 'motion_sensor_start') as mock_start:
            plugin.on_event('print_started', {})
            mock_start.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_on_event_print_done(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test event handling for print done"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        with patch.object(plugin, 'motion_sensor_stop_thread') as mock_stop:
            plugin.on_event('print_done', {})
            mock_stop.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_on_event_print_failed(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test event handling for print failed"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        with patch.object(plugin, 'motion_sensor_stop_thread') as mock_stop:
            plugin.on_event('print_failed', {})
            mock_stop.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_on_event_print_cancelled(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test event handling for print cancelled"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        with patch.object(plugin, 'motion_sensor_stop_thread') as mock_stop:
            plugin.on_event('print_cancelled', {})
            mock_stop.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_get_template_configs(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test template configuration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        configs = plugin.get_template_configs()
        
        assert len(configs) == 1
        assert configs[0]['type'] == 'settings'
        assert configs[0]['custom_bindings'] == True

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_get_assets(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test asset configuration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        assets = plugin.get_assets()
        
        assert 'js' in assets
        assert 'js/filamentmotionsensor_sidebar.js' in assets['js']
        assert 'js/filamentmotionsensor_settings.js' in assets['js']

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_get_api_commands(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test API command configuration"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        commands = plugin.get_api_commands()
        
        expected_commands = [
            'testSensor', 'stopConnectionTest', 'getSensorData', 
            'sendTestGcode', 'testCustomGcode'
        ]
        
        for cmd in expected_commands:
            assert cmd in commands

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_on_api_command_get_sensor_data(self, mock_jsonify, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test API command for getting sensor data"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_jsonify.return_value = {'test': 'data'}
        
        result = plugin.on_api_command('getSensorData', {})
        
        mock_jsonify.assert_called_once()
        assert result == {'test': 'data'}

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    @patch('flask.jsonify')
    def test_on_api_command_test_sensor(self, mock_jsonify, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test API command for testing sensor"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        mock_jsonify.return_value = {'status': 'ok'}
        
        with patch.object(plugin, 'start_connection_test') as mock_test:
            result = plugin.on_api_command('testSensor', {})
            mock_test.assert_called_once()
            mock_jsonify.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_on_settings_save(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test settings save handling"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        with patch.object(plugin, '_setup_sensor') as mock_setup:
            plugin.on_settings_save({'motion_sensor_pin': 18})
            mock_setup.assert_called_once()

    @patch('octoprint_filamentmotionsensor.MotionSensorGPIOThread')
    @patch('octoprint_filamentmotionsensor.FilamentMotionSensorDetectionData')
    def test_on_after_startup(self, mock_data_class, mock_thread_class, mock_octoprint_plugin):
        """Test after startup handling"""
        from octoprint_filamentmotionsensor import FilamentMotionSensor
        
        plugin = FilamentMotionSensor()
        plugin._logger = self.mock_logger
        plugin._settings = self.mock_settings
        plugin._printer = self.mock_printer
        plugin.initialize()
        
        with patch.object(plugin, '_setup_sensor') as mock_setup:
            plugin.on_after_startup()
            mock_setup.assert_called_once()
            self.mock_logger.info.assert_called_with("Filament Motion Sensor started") 