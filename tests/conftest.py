import pytest
from unittest.mock import Mock, MagicMock, patch
import time
import threading
import tempfile
import os


@pytest.fixture
def mock_octoprint_plugin():
    """Mock OctoPrint plugin base classes"""
    with patch('octoprint.plugin.StartupPlugin'), \
         patch('octoprint.plugin.EventHandlerPlugin'), \
         patch('octoprint.plugin.TemplatePlugin'), \
         patch('octoprint.plugin.SettingsPlugin'), \
         patch('octoprint.plugin.AssetPlugin'), \
         patch('octoprint.plugin.SimpleApiPlugin'):
        yield


@pytest.fixture
def mock_octoprint_events():
    """Mock OctoPrint Events"""
    with patch('octoprint.events.Events') as mock_events:
        mock_events.PRINT_STARTED = 'print_started'
        mock_events.PRINT_DONE = 'print_done'
        mock_events.PRINT_FAILED = 'print_failed'
        mock_events.PRINT_CANCELLED = 'print_cancelled'
        mock_events.PRINT_PAUSED = 'print_paused'
        mock_events.PRINT_RESUMED = 'print_resumed'
        mock_events.Z_CHANGE = 'z_change'
        yield mock_events


@pytest.fixture
def mock_logger():
    """Mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warn = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_settings():
    """Mock OctoPrint settings"""
    settings = Mock()
    settings_dict = {
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
    
    settings.get = Mock(side_effect=lambda keys: settings_dict.get(keys[0]))
    settings.get_boolean = Mock(side_effect=lambda keys: settings_dict.get(keys[0]))
    settings.set = Mock()
    return settings


@pytest.fixture
def mock_printer():
    """Mock OctoPrint printer"""
    printer = Mock()
    printer.is_printing = Mock(return_value=False)
    printer.is_paused = Mock(return_value=False)
    printer.commands = Mock()
    printer.pause_print = Mock()
    printer.cancel_print = Mock()
    return printer


@pytest.fixture
def mock_gpiod():
    """Mock gpiod library"""
    with patch('gpiod.Chip') as mock_chip_class, \
         patch('gpiod.request_lines') as mock_request_lines, \
         patch('gpiod.is_gpiochip_device') as mock_is_gpiochip, \
         patch('gpiod.LineSettings') as mock_line_settings, \
         patch('select.poll') as mock_poll:
        
        # Mock chip
        mock_chip = Mock()
        mock_chip_class.return_value = mock_chip
        mock_is_gpiochip.return_value = True
        
        # Mock request lines
        mock_request = Mock()
        mock_request.fd = 123
        mock_request.wait_edge_events = Mock(return_value=False)
        mock_request.read_edge_events = Mock(return_value=[])
        mock_request.__enter__ = Mock(return_value=mock_request)
        mock_request.__exit__ = Mock(return_value=None)
        mock_request_lines.return_value = mock_request
        
        # Mock poll
        mock_poll_instance = Mock()
        mock_poll_instance.register = Mock()
        mock_poll_instance.unregister = Mock()
        mock_poll_instance.poll = Mock()
        mock_poll.return_value = mock_poll_instance
        
        yield {
            'chip_class': mock_chip_class,
            'chip': mock_chip,
            'request_lines': mock_request_lines,
            'request': mock_request,
            'is_gpiochip': mock_is_gpiochip,
            'line_settings': mock_line_settings,
            'poll': mock_poll,
            'poll_instance': mock_poll_instance
        }


@pytest.fixture
def mock_revision_file():
    """Mock Raspberry Pi revision file"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Write a sample revision (RPi 4B)
        f.write(b'\x00\xa0\x31\x11')
        f.flush()
        
        with patch('builtins.open', mock_open_revision_file(f.name)):
            yield f.name
        
        os.unlink(f.name)


def mock_open_revision_file(filename):
    """Helper to mock opening revision file"""
    def mock_open(path, mode='r'):
        if path == "/proc/device-tree/system/linux,revision":
            return open(filename, mode)
        return open(path, mode)
    return mock_open


@pytest.fixture
def mock_flask():
    """Mock Flask"""
    with patch('flask.jsonify') as mock_jsonify, \
         patch('flask.request') as mock_request:
        mock_jsonify.side_effect = lambda x: x
        mock_request.json = {}
        yield {'jsonify': mock_jsonify, 'request': mock_request}


@pytest.fixture
def sample_data():
    """Sample data for tests"""
    return {
        'remaining_distance': 7,
        'absolut_extrusion': True,
        'flag': 10,
        'lastE': 5.0,
        'currentE': 10.0,
        'last_motion_detected': time.time(),
        'filament_moving': True,
        'connection_test_running': False
    }


@pytest.fixture
def mock_time():
    """Mock time.time() for consistent testing"""
    with patch('time.time') as mock_time_func:
        mock_time_func.return_value = 1234567890.0
        yield mock_time_func


@pytest.fixture
def mock_threading():
    """Mock threading for controlled test execution"""
    with patch('threading.Thread') as mock_thread:
        mock_thread_instance = Mock()
        mock_thread_instance.start = Mock()
        mock_thread_instance.join = Mock()
        mock_thread_instance.is_alive = Mock(return_value=False)
        mock_thread.return_value = mock_thread_instance
        yield mock_thread_instance


@pytest.fixture
def plugin_instance(mock_octoprint_plugin, mock_logger, mock_settings, mock_printer):
    """Create a plugin instance for testing"""
    # Need to import after mocking
    from octoprint_filamentmotionsensor import FilamentMotionSensor
    
    plugin = FilamentMotionSensor()
    plugin._logger = mock_logger
    plugin._settings = mock_settings
    plugin._printer = mock_printer
    plugin.initialize()
    
    return plugin


@pytest.fixture
def data_instance(sample_data):
    """Create a data instance for testing"""
    from octoprint_filamentmotionsensor.data import FilamentMotionSensorDetectionData
    
    mock_callback = Mock()
    data = FilamentMotionSensorDetectionData(
        sample_data['remaining_distance'],
        sample_data['absolut_extrusion'],
        mock_callback
    )
    return data 