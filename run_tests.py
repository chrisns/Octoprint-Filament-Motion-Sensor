#!/usr/bin/env python3
"""
Test runner for OctoPrint Filament Motion Sensor Plugin
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0

def install_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    
    # Install test requirements
    cmd = [sys.executable, "-m", "pip", "install", "-r", "test-requirements.txt"]
    if not run_command(cmd, "Installing test dependencies"):
        return False
    
    # Install plugin in development mode
    cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    if not run_command(cmd, "Installing plugin in development mode"):
        return False
    
    return True

def run_tests(test_type="all", verbose=False, coverage=True):
    """Run tests based on type"""
    
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        base_cmd.append("-v")
    
    if coverage:
        base_cmd.extend([
            "--cov=octoprint_filamentmotionsensor",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    if test_type == "unit":
        base_cmd.extend(["-m", "unit", "tests/"])
    elif test_type == "integration":
        base_cmd.extend(["-m", "integration", "tests/"])
    elif test_type == "fast":
        base_cmd.extend(["-m", "not slow", "tests/"])
    elif test_type == "all":
        base_cmd.append("tests/")
    else:
        # Run specific test file or pattern
        base_cmd.append(test_type)
    
    return run_command(base_cmd, f"Running {test_type} tests")

def run_linting():
    """Run code linting"""
    print("Running code linting...")
    success = True

    # Check if flake8 is available
    try:
        import flake8
        cmd = [sys.executable, "-m", "flake8", "octoprint_filamentmotionsensor/", "tests/"]
        if not run_command(cmd, "Running flake8 linting"):
            success = False
    except ImportError:
        print("flake8 not available, skipping linting")

    return success


def run_formatting_check():
    """Run code formatting checks"""
    print("Running code formatting checks...")
    success = True

    # Check Black formatting
    try:
        import black

        cmd = [sys.executable, "-m", "black", "--check", "--diff", "octoprint_filamentmotionsensor/", "tests/"]
        if not run_command(cmd, "Checking Black formatting"):
            print("💡 Run 'black octoprint_filamentmotionsensor/ tests/' to fix formatting")
            success = False
    except ImportError:
        print("black not available, skipping Black check")

    # Check isort formatting
    try:
        import isort

        cmd = [sys.executable, "-m", "isort", "--check-only", "--diff", "octoprint_filamentmotionsensor/", "tests/"]
        if not run_command(cmd, "Checking isort import sorting"):
            print("💡 Run 'isort octoprint_filamentmotionsensor/ tests/' to fix import sorting")
            success = False
    except ImportError:
        print("isort not available, skipping isort check")

    return success


def run_security_checks():
    """Run security checks"""
    print("Running security checks...")
    success = True

    # Run bandit security check
    try:
        import bandit

        cmd = [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            "octoprint_filamentmotionsensor/",
            "-f",
            "json",
            "-o",
            "bandit-report.json",
        ]
        if not run_command(cmd, "Running bandit security check"):
            success = False
    except ImportError:
        print("bandit not available, skipping security check")

    # Run safety dependency check
    try:
        import safety

        cmd = [sys.executable, "-m", "safety", "check", "--json", "--output", "safety-report.json"]
        if not run_command(cmd, "Running safety dependency check"):
            success = False
    except ImportError:
        print("safety not available, skipping dependency check")

    return success


def run_type_checking():
    """Run type checking"""
    print("Running type checking...")

    try:
        import mypy

        cmd = [sys.executable, "-m", "mypy", "octoprint_filamentmotionsensor/"]
        return run_command(cmd, "Running mypy type checking")
    except ImportError:
        print("mypy not available, skipping type checking")
        return True


def format_code():
    """Format code using Black and isort"""
    print("Formatting code...")
    success = True

    # Format with Black
    try:
        import black

        cmd = [sys.executable, "-m", "black", "octoprint_filamentmotionsensor/", "tests/"]
        if not run_command(cmd, "Formatting code with Black"):
            success = False
    except ImportError:
        print("black not available, skipping Black formatting")

    # Sort imports with isort
    try:
        import isort

        cmd = [sys.executable, "-m", "isort", "octoprint_filamentmotionsensor/", "tests/"]
        if not run_command(cmd, "Sorting imports with isort"):
            success = False
    except ImportError:
        print("isort not available, skipping import sorting")

    return success


def generate_coverage_report():
    """Generate coverage report"""
    print("Generating coverage report...")

    cmd = [sys.executable, "-m", "coverage", "html"]
    if run_command(cmd, "Generating HTML coverage report"):
        print("Coverage report generated in htmlcov/index.html")
        return True

    return False


def validate_plugin():
    """Validate plugin can be imported"""
    print("Validating plugin imports...")

    try:
        import octoprint_filamentmotionsensor

        print("✅ Plugin imports successfully")

        from octoprint_filamentmotionsensor import FilamentMotionSensor

        print("✅ Main class imports successfully")

        from octoprint_filamentmotionsensor.SensorGPIOThread import MotionSensorGPIOThread

        print("✅ GPIO thread imports successfully")

        from octoprint_filamentmotionsensor.data import FilamentMotionSensorDetectionData

        print("✅ Data class imports successfully")

        return True
    except ImportError as e:
        print(f"❌ Plugin import failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for OctoPrint Filament Motion Sensor Plugin")

    parser.add_argument("--install", action="store_true", 
                       help="Install test dependencies")
    parser.add_argument("--type", choices=["all", "unit", "integration", "fast"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--test", type=str, help="Specific test file or pattern to run")
    parser.add_argument("--no-coverage", action="store_true", 
                       help="Skip coverage reporting")
    parser.add_argument("--lint", action="store_true", 
                       help="Run linting checks")
    parser.add_argument("--format", action="store_true", help="Format code with Black and isort")
    parser.add_argument("--format-check", action="store_true", help="Check code formatting")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--validate", action="store_true", help="Validate plugin imports")
    parser.add_argument(
        "--all-checks", action="store_true", help="Run all quality checks (lint, format-check, security, type-check)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage-report", action="store_true", 
                       help="Generate HTML coverage report")

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    success = True

    # Install dependencies if requested
    if args.install:
        success &= install_dependencies()

    # Format code if requested
    if args.format:
        success &= format_code()

    # Run all quality checks if requested
    if args.all_checks:
        args.lint = True
        args.format_check = True
        args.security = True
        args.type_check = True
        args.validate = True

    # Run formatting check if requested
    if args.format_check:
        success &= run_formatting_check()

    # Run linting if requested
    if args.lint:
        success &= run_linting()

    # Run security checks if requested
    if args.security:
        success &= run_security_checks()

    # Run type checking if requested
    if args.type_check:
        success &= run_type_checking()

    # Validate plugin if requested
    if args.validate:
        success &= validate_plugin()

    # Run tests
    if args.test:
        success &= run_tests(args.test, args.verbose, not args.no_coverage)
    else:
        success &= run_tests(args.type, args.verbose, not args.no_coverage)

    # Generate coverage report if requested
    if args.coverage_report and not args.no_coverage:
        success &= generate_coverage_report()

    if success:
        print("\n✅ All operations completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some operations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 
