import pytest
import json
from unittest.mock import Mock
import time
from octoprint_filamentmotionsensor.data import FilamentMotionSensorDetectionData


class TestFilamentMotionSensorDetectionData:
    """Test suite for FilamentMotionSensorDetectionData class"""

    def test_initialization(self):
        """Test proper initialization of the data object"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(10, True, callback)
        
        assert data.remaining_distance == 10
        assert data.absolut_extrusion == True
        assert data.callbackUpdateUI == callback
        assert data.START_DISTANCE_OFFSET == 7
        assert data.flag == -1
        assert data.lastE == -1
        assert data.currentE == -1
        assert data.last_motion_detected == ""
        assert data.filament_moving == False

    def test_remaining_distance_property(self):
        """Test remaining_distance property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test getter
        assert data.remaining_distance == 5
        
        # Test setter
        data.remaining_distance = 15
        assert data.remaining_distance == 15
        
        # Test that callback is called when value changes
        callback.assert_called()

    def test_flag_property(self):
        """Test flag property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test initial value
        assert data.flag == -1
        
        # Test setter
        data.flag = 10
        assert data.flag == 10
        
        # Test that callback is called when value changes
        callback.assert_called()

    def test_lastE_property(self):
        """Test lastE property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test initial value
        assert data.lastE == -1
        
        # Test setter
        data.lastE = 5.5
        assert data.lastE == 5.5
        
        # Note: lastE doesn't trigger callback

    def test_currentE_property(self):
        """Test currentE property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test initial value
        assert data.currentE == -1
        
        # Test setter
        data.currentE = 10.5
        assert data.currentE == 10.5
        
        # Note: currentE doesn't trigger callback

    def test_absolut_extrusion_property(self):
        """Test absolut_extrusion property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, False, callback)
        
        # Test initial value
        assert data.absolut_extrusion == False
        
        # Test setter
        data.absolut_extrusion = True
        assert data.absolut_extrusion == True

    def test_last_motion_detected_property(self):
        """Test last_motion_detected property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test initial value
        assert data.last_motion_detected == ""
        
        # Test setter
        current_time = time.time()
        data.last_motion_detected = current_time
        assert data.last_motion_detected == current_time
        
        # Test that callback is called when value changes
        callback.assert_called()

    def test_filament_moving_property(self):
        """Test filament_moving property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test initial value
        assert data.filament_moving == False
        
        # Test setter
        data.filament_moving = True
        assert data.filament_moving == True
        
        # Test that callback is called when value changes
        callback.assert_called()

    def test_connection_test_running_property(self):
        """Test connection_test_running property getter and setter"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Test default value (should be False)
        assert data.connection_test_running == False
        
        # Test setter
        data.connection_test_running = True
        assert data.connection_test_running == True
        
        # Test that callback is called when value changes
        callback.assert_called()

    def test_callback_functionality(self):
        """Test that callback is called appropriately"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Reset call count
        callback.reset_mock()
        
        # Test properties that should trigger callback
        callback_triggering_properties = [
            ('remaining_distance', 15),
            ('flag', 20),
            ('last_motion_detected', time.time()),
            ('filament_moving', True),
            ('connection_test_running', True)
        ]
        
        for prop_name, value in callback_triggering_properties:
            callback.reset_mock()
            setattr(data, prop_name, value)
            callback.assert_called_once()

    def test_callback_not_triggered_for_non_ui_properties(self):
        """Test that callback is not called for properties that don't affect UI"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Reset call count
        callback.reset_mock()
        
        # Test properties that should NOT trigger callback
        non_callback_properties = [
            ('lastE', 5.5),
            ('currentE', 10.5),
            ('absolut_extrusion', False)
        ]
        
        for prop_name, value in non_callback_properties:
            callback.reset_mock()
            setattr(data, prop_name, value)
            callback.assert_not_called()

    def test_toJSON_method(self):
        """Test JSON serialization"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Set some values
        data.remaining_distance = 12
        data.flag = 25
        data.lastE = 7.5
        data.currentE = 12.5
        data.absolut_extrusion = False
        data.last_motion_detected = 1234567890.0
        data.filament_moving = True
        data.connection_test_running = False
        
        # Test JSON serialization
        json_output = data.toJSON()
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        
        # Check that all properties are included
        assert '_remaining_distance' in parsed
        assert '_flag' in parsed
        assert '_lastE' in parsed
        assert '_currentE' in parsed
        assert '_absolut_extrusion' in parsed
        assert '_last_motion_detected' in parsed
        assert '_filament_moving' in parsed
        assert 'START_DISTANCE_OFFSET' in parsed
        assert 'callbackUpdateUI' in parsed
        
        # Check values
        assert parsed['_remaining_distance'] == 12
        assert parsed['_flag'] == 25
        assert parsed['_lastE'] == 7.5
        assert parsed['_currentE'] == 12.5
        assert parsed['_absolut_extrusion'] == False
        assert parsed['_last_motion_detected'] == 1234567890.0
        assert parsed['_filament_moving'] == True
        assert parsed['START_DISTANCE_OFFSET'] == 7

    def test_no_callback_initialization(self):
        """Test initialization without callback"""
        data = FilamentMotionSensorDetectionData(5, True, None)
        
        assert data.remaining_distance == 5
        assert data.absolut_extrusion == True
        assert data.callbackUpdateUI == None
        
        # Should not crash when trying to call None callback
        data.remaining_distance = 10
        assert data.remaining_distance == 10

    def test_multiple_property_changes(self):
        """Test multiple property changes in sequence"""
        callback = Mock()
        data = FilamentMotionSensorDetectionData(5, True, callback)
        
        # Change multiple properties
        data.remaining_distance = 15
        data.flag = 30
        data.filament_moving = True
        data.connection_test_running = True
        
        # Check final values
        assert data.remaining_distance == 15
        assert data.flag == 30
        assert data.filament_moving == True
        assert data.connection_test_running == True
        
        # Callback should have been called for each property change
        assert callback.call_count == 4 