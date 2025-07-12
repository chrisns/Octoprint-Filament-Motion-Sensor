import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from octoprint_filamentmotionsensor.SensorGPIOThread import (
    MotionSensorGPIOThread,
    get_revision,
    processor,
    type as get_type,
    plugin_check_rpi_gpio
)
from octoprint_filamentmotionsensor.data import FilamentMotionSensorDetectionData


class TestRaspberryPiHelperFunctions:
    """Test suite for Raspberry Pi detection helper functions"""

    def test_get_revision_rpi4(self, mock_revision_file):
        """Test getting revision for RPi 4"""
        with patch('builtins.open', mock_open=Mock(return_value=Mock(read=Mock(return_value=b'\x00\xa0\x31\x11')))):
            revision = get_revision()
            assert revision == 0x00a03111

    def test_get_revision_rpi5(self):
        """Test getting revision for RPi 5"""
        with patch('builtins.open', mock_open=Mock(return_value=Mock(read=Mock(return_value=b'\x00\xc0\x41\x17')))):
            revision = get_revision()
            assert revision == 0x00c04117

    def test_processor_bcm2835(self):
        """Test processor detection for BCM2835"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00900092):
            proc = processor()
            assert proc == 0  # BCM2835

    def test_processor_bcm2711(self):
        """Test processor detection for BCM2711"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            proc = processor()
            assert proc == 3  # BCM2711

    def test_processor_bcm2712(self):
        """Test processor detection for BCM2712"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00c04117):
            proc = processor()
            assert proc == 4  # BCM2712

    def test_type_detection_rpi4(self):
        """Test type detection for RPi 4"""
        revision = 0x00a03111  # RPi 4B
        rpi_type = get_type(revision)
        assert rpi_type == 0x11  # 4B

    def test_type_detection_rpi5(self):
        """Test type detection for RPi 5"""
        revision = 0x00c04117  # RPi 5
        rpi_type = get_type(revision)
        assert rpi_type == 0x17  # 5

    def test_type_detection_rpi_zero(self):
        """Test type detection for RPi Zero"""
        revision = 0x00900092  # RPi Zero
        rpi_type = get_type(revision)
        assert rpi_type == 0x09  # Zero

    def test_plugin_check_rpi_gpio_success(self, mock_gpiod):
        """Test successful GPIO chip detection"""
        mock_gpiod['is_gpiochip'].return_value = True
        
        result = plugin_check_rpi_gpio()
        assert result == True

    def test_plugin_check_rpi_gpio_failure(self, mock_gpiod):
        """Test failed GPIO chip detection"""
        mock_gpiod['chip_class'].side_effect = Exception("GPIO chip not found")
        
        result = plugin_check_rpi_gpio()
        assert result == False

    def test_plugin_check_rpi_gpio_not_gpiochip(self, mock_gpiod):
        """Test when device is not a GPIO chip"""
        mock_gpiod['is_gpiochip'].return_value = False
        
        result = plugin_check_rpi_gpio()
        assert result == False


class TestMotionSensorGPIOThread:
    """Test suite for MotionSensorGPIOThread class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()
        self.mock_callback = Mock()
        self.mock_data = Mock()
        self.mock_data.last_motion_detected = time.time()

    def test_initialization_rpi4(self, mock_gpiod):
        """Test thread initialization for RPi 4"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            assert thread.threadID == 1
            assert thread.name == "TestThread"
            assert thread.used_pin == 17
            assert thread.max_not_moving_time == 5
            assert thread.chip_address == '/dev/gpiochip0'
            assert thread.keepRunning == True

    def test_initialization_rpi5(self, mock_gpiod):
        """Test thread initialization for RPi 5"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00c04117):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            assert thread.chip_address == '/dev/gpiochip4'

    def test_initialization_gpio_chip_failure(self, mock_gpiod):
        """Test thread initialization when GPIO chip fails"""
        mock_gpiod['chip_class'].side_effect = Exception("GPIO chip error")
        
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            assert thread.used_pin == -1
            self.mock_logger.error.assert_called_with("GPIO Chip address is wrong")

    def test_run_method_motion_detected(self, mock_gpiod):
        """Test run method when motion is detected"""
        # Mock edge event
        mock_event = Mock()
        mock_event.line_offset = 17
        mock_event.line_seqno = 1
        
        # Configure mocks
        mock_gpiod['request'].wait_edge_events.side_effect = [True, False, False]
        mock_gpiod['request'].read_edge_events.return_value = [mock_event]
        
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 1, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            # Mock time to control loop
            with patch('time.time', side_effect=[1000, 1001, 1002, 1003]):
                # Start thread but stop it quickly
                thread.keepRunning = True
                
                # Create a side effect to stop the thread after first iteration
                def stop_thread(*args):
                    thread.keepRunning = False
                
                mock_gpiod['poll_instance'].poll.side_effect = stop_thread
                
                # Run the thread
                thread.run()
                
                # Verify motion callback was called
                self.mock_callback.assert_called_with(True)

    def test_run_method_timeout_detection(self, mock_gpiod):
        """Test run method timeout detection"""
        # Mock no motion for extended time
        mock_gpiod['request'].wait_edge_events.return_value = False
        
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 1, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            # Mock time progression
            start_time = 1000
            self.mock_data.last_motion_detected = start_time
            
            with patch('time.time', side_effect=[start_time, start_time + 2, start_time + 3]):
                thread.keepRunning = True
                
                # Create a side effect to stop the thread after checking timeout
                def stop_thread(*args):
                    thread.keepRunning = False
                
                mock_gpiod['poll_instance'].poll.side_effect = stop_thread
                
                # Run the thread
                thread.run()
                
                # Verify timeout callback was called
                self.mock_callback.assert_called_with(False)

    def test_run_method_no_timeout(self, mock_gpiod):
        """Test run method when no timeout occurs"""
        # Mock no motion but within timeout
        mock_gpiod['request'].wait_edge_events.return_value = False
        
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            # Mock time progression within timeout
            start_time = 1000
            self.mock_data.last_motion_detected = start_time
            
            with patch('time.time', side_effect=[start_time, start_time + 1, start_time + 2]):
                thread.keepRunning = True
                
                # Create a side effect to stop the thread
                def stop_thread(*args):
                    thread.keepRunning = False
                
                mock_gpiod['poll_instance'].poll.side_effect = stop_thread
                
                # Run the thread
                thread.run()
                
                # Verify no timeout callback was called
                # (Only the False callback should not be called)
                if self.mock_callback.called:
                    # If callback was called, it should be with True (motion detected)
                    self.mock_callback.assert_called_with(True)

    def test_run_method_wrong_pin_event(self, mock_gpiod):
        """Test run method ignoring events from wrong pin"""
        # Mock edge event from different pin
        mock_event = Mock()
        mock_event.line_offset = 18  # Different pin
        mock_event.line_seqno = 1
        
        # Configure mocks
        mock_gpiod['request'].wait_edge_events.side_effect = [True, False]
        mock_gpiod['request'].read_edge_events.return_value = [mock_event]
        
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            thread.keepRunning = True
            
            # Create a side effect to stop the thread
            def stop_thread(*args):
                thread.keepRunning = False
            
            mock_gpiod['poll_instance'].poll.side_effect = stop_thread
            
            # Run the thread
            thread.run()
            
            # Verify callback was not called for wrong pin
            self.mock_callback.assert_not_called()

    def test_run_method_cleanup(self, mock_gpiod):
        """Test run method cleanup"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            thread.keepRunning = True
            
            # Create a side effect to stop the thread immediately
            def stop_thread(*args):
                thread.keepRunning = False
            
            mock_gpiod['poll_instance'].poll.side_effect = stop_thread
            
            # Run the thread
            thread.run()
            
            # Verify cleanup was called
            mock_gpiod['poll_instance'].unregister.assert_called_once()

    def test_run_method_multiple_events(self, mock_gpiod):
        """Test run method handling multiple events"""
        # Mock multiple edge events
        mock_event1 = Mock()
        mock_event1.line_offset = 17
        mock_event1.line_seqno = 1
        
        mock_event2 = Mock()
        mock_event2.line_offset = 17
        mock_event2.line_seqno = 2
        
        # Configure mocks
        mock_gpiod['request'].wait_edge_events.side_effect = [True, False]
        mock_gpiod['request'].read_edge_events.return_value = [mock_event1, mock_event2]
        
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            thread.keepRunning = True
            
            # Create a side effect to stop the thread
            def stop_thread(*args):
                thread.keepRunning = False
            
            mock_gpiod['poll_instance'].poll.side_effect = stop_thread
            
            # Run the thread
            thread.run()
            
            # Verify callback was called for each event
            assert self.mock_callback.call_count == 2
            self.mock_callback.assert_called_with(True)

    def test_thread_as_thread_object(self, mock_gpiod):
        """Test that MotionSensorGPIOThread can be used as a proper thread"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            # Verify it's a thread
            assert isinstance(thread, threading.Thread)
            assert thread.name == "TestThread"
            assert thread.daemon == False  # Default value
            
            # Test that it can be started (we won't actually run it)
            thread.keepRunning = False  # Prevent actual running
            
            # Mock the run method to prevent actual execution
            with patch.object(thread, 'run'):
                thread.start()
                # Thread should start without error

    def test_thread_keep_running_control(self, mock_gpiod):
        """Test keepRunning flag controls thread execution"""
        with patch('octoprint_filamentmotionsensor.SensorGPIOThread.get_revision', return_value=0x00a03111):
            thread = MotionSensorGPIOThread(
                1, "TestThread", 17, 5, 
                self.mock_logger, self.mock_data, self.mock_callback
            )
            
            # Test keepRunning is initially True
            assert thread.keepRunning == True
            
            # Test setting keepRunning to False
            thread.keepRunning = False
            assert thread.keepRunning == False 