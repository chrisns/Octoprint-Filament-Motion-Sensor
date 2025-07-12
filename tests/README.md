# OctoPrint Filament Motion Sensor Plugin - Test Suite

This directory contains comprehensive tests for the OctoPrint Filament Motion Sensor Plugin. The tests are designed to validate all aspects of the plugin's functionality without requiring actual hardware.

## Test Structure

### Test Files

- `conftest.py` - Pytest configuration and shared fixtures
- `test_data_models.py` - Tests for data models and structures
- `test_gpio_thread.py` - Tests for GPIO thread functionality and Raspberry Pi detection
- `test_main_plugin.py` - Tests for the main plugin class and core functionality
- `test_sensor_logic.py` - Tests for sensor logic, status flags, and calculations
- `test_api_commands.py` - Tests for API commands and responses
- `test_integration.py` - Integration tests for event handling and workflows

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Mocked Tests**: All tests use mocks to avoid hardware dependencies

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r test-requirements.txt
```

2. Install the plugin in development mode:
```bash
pip install -e .
```

### Quick Start

Run all tests:
```bash
python run_tests.py
```

Or use pytest directly:
```bash
pytest tests/
```

### Test Runner Options

The `run_tests.py` script provides several options:

```bash
# Install dependencies and run all tests
python run_tests.py --install

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type fast

# Run specific test file
python run_tests.py --test tests/test_data_models.py

# Run with verbose output
python run_tests.py --verbose

# Skip coverage reporting
python run_tests.py --no-coverage

# Run linting
python run_tests.py --lint

# Generate HTML coverage report
python run_tests.py --coverage-report
```

### Direct pytest Usage

```bash
# Run all tests with coverage
pytest tests/ --cov=octoprint_filamentmotionsensor --cov-report=html

# Run specific test file
pytest tests/test_data_models.py -v

# Run tests matching a pattern
pytest tests/ -k "test_sensor" -v

# Run tests with specific markers
pytest tests/ -m "unit" -v
```

## Test Coverage

The test suite aims for high code coverage across all components:

### Coverage Areas

1. **Data Models** (90%+ coverage)
   - Property getters and setters
   - Callback functionality
   - JSON serialization
   - Edge cases and error conditions

2. **GPIO Thread** (85%+ coverage)
   - Thread initialization and cleanup
   - Event detection and handling
   - Timeout detection
   - Raspberry Pi version detection
   - Error handling

3. **Main Plugin** (80%+ coverage)
   - Plugin initialization and setup
   - Event handling
   - Settings management
   - API command processing
   - Distance and timeout calculations

4. **Sensor Logic** (85%+ coverage)
   - Status flag transitions
   - Distance calculations
   - Timeout detection
   - Custom gcode handling
   - Temperature monitoring

5. **API Commands** (90%+ coverage)
   - All API endpoints
   - Parameter validation
   - Error handling
   - Response formatting

6. **Integration** (75%+ coverage)
   - Print workflow
   - Event sequences
   - Error recovery
   - State persistence

### Coverage Reports

After running tests with coverage, reports are generated in:
- Terminal: Summary with missing lines
- HTML: `htmlcov/index.html` - Interactive HTML report
- XML: `coverage.xml` - For CI/CD integration

## Test Fixtures and Mocking

### Key Fixtures

- `mock_octoprint_plugin` - Mocks OctoPrint plugin base classes
- `mock_gpiod` - Mocks GPIO library functionality
- `mock_logger` - Mocks OctoPrint logger
- `mock_settings` - Mocks OctoPrint settings
- `mock_printer` - Mocks OctoPrint printer interface
- `plugin_instance` - Pre-configured plugin instance for testing
- `data_instance` - Pre-configured data instance for testing

### Mocking Strategy

All tests use comprehensive mocking to:
- Avoid hardware dependencies
- Ensure consistent test environments
- Test error conditions safely
- Validate interactions between components

## Test Data and Scenarios

### Test Scenarios Covered

1. **Normal Operation**
   - Plugin initialization
   - Print start/stop cycles
   - Motion detection
   - Distance calculations

2. **Error Conditions**
   - GPIO initialization failures
   - Invalid settings
   - Hardware disconnection
   - Communication errors

3. **Edge Cases**
   - Rapid state changes
   - Concurrent operations
   - Boundary conditions
   - Resource cleanup

4. **Integration Workflows**
   - Complete print workflows
   - Filament jam detection
   - Pause/resume cycles
   - Settings changes

### Test Data

- Sample sensor readings
- Mock GPIO events
- Simulated printer states
- Test gcode sequences
- Configuration variations

## Continuous Integration

The test suite is designed for CI/CD environments:

### CI Configuration

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python run_tests.py --install
    python run_tests.py --lint
    python run_tests.py --type all
    python run_tests.py --coverage-report
```

### Quality Gates

- Minimum 80% code coverage
- All tests must pass
- No linting errors
- No deprecation warnings

## Debugging Tests

### Common Issues

1. **Import Errors**: Ensure plugin is installed in development mode
2. **Mock Failures**: Check fixture setup and patch targets
3. **Coverage Issues**: Verify test file patterns and imports

### Debugging Tips

```bash
# Run specific test with detailed output
pytest tests/test_data_models.py::TestFilamentMotionSensorDetectionData::test_initialization -v -s

# Run tests with pdb debugger
pytest tests/test_data_models.py --pdb

# Show print statements
pytest tests/test_data_models.py -s
```

## Contributing to Tests

### Adding New Tests

1. Follow existing naming conventions
2. Use appropriate fixtures
3. Add docstrings to test methods
4. Include both positive and negative test cases
5. Mock external dependencies

### Test Structure

```python
def test_feature_description(self, fixture1, fixture2):
    """Test description explaining what is being tested"""
    # Arrange
    setup_test_data()
    
    # Act
    result = perform_operation()
    
    # Assert
    assert result == expected_value
    verify_interactions()
```

### Best Practices

- Keep tests focused and atomic
- Use descriptive test names
- Test both success and failure paths
- Verify mock interactions
- Clean up resources in teardown

## Performance Considerations

### Test Execution Time

- Unit tests: < 1 second each
- Integration tests: < 5 seconds each
- Full suite: < 30 seconds

### Optimization Tips

- Use pytest markers to categorize tests
- Run fast tests frequently
- Use parallel execution for large suites
- Cache fixture setup when possible

## Hardware Testing

While these tests use mocks, for actual hardware validation:

1. Use `octoprint_filamentmotionsensor/sensor_gpiod_check.py` for GPIO testing
2. Set up test hardware with known sensor configurations
3. Run integration tests on actual printer setups
4. Validate against different Raspberry Pi models

## Support and Troubleshooting

For test-related issues:

1. Check the test output for specific error messages
2. Verify all dependencies are installed
3. Ensure Python environment is properly configured
4. Review fixture setup and mock configurations

The test suite provides a solid foundation for ensuring the plugin works correctly across various scenarios and configurations. 