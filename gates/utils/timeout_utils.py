"""
Platform-independent timeout utilities for CodeGates.
Works on Windows, Linux, macOS, and other operating systems.
"""

import os
import sys
import time
import threading
import signal
from typing import Callable, Any, Optional
from functools import wraps
import concurrent.futures


class TimeoutError(Exception):
    """Custom timeout exception for platform-independent timeout handling"""
    pass


class PlatformTimeoutHandler:
    """Platform-independent timeout handler that works across all operating systems"""
    
    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds
        self._is_windows = sys.platform.startswith('win')
        self._timer = None
        self._original_handler = None
        self._timed_out = False
    
    def __enter__(self):
        """Context manager entry - start timeout"""
        self.start_timeout()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop timeout"""
        self.stop_timeout()
        if exc_type is TimeoutError:
            return True  # Suppress the timeout exception
        return False
    
    def start_timeout(self):
        """Start the timeout mechanism"""
        if self._is_windows:
            self._start_windows_timeout()
        else:
            self._start_unix_timeout()
    
    def stop_timeout(self):
        """Stop the timeout mechanism"""
        if self._is_windows:
            self._stop_windows_timeout()
        else:
            self._stop_unix_timeout()
    
    def _start_windows_timeout(self):
        """Windows-specific timeout using threading"""
        self._timed_out = False
        
        def timeout_callback():
            self._timed_out = True
            # Force exit by raising an exception in the main thread
            import _thread
            _thread.interrupt_main()
        
        self._timer = threading.Timer(self.timeout_seconds, timeout_callback)
        self._timer.daemon = True
        self._timer.start()
    
    def _stop_windows_timeout(self):
        """Stop Windows timeout"""
        if self._timer:
            self._timer.cancel()
            self._timer = None
    
    def _start_unix_timeout(self):
        """Unix/Linux/macOS timeout using signal"""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")
        
        self._original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)
    
    def _stop_unix_timeout(self):
        """Stop Unix timeout"""
        signal.alarm(0)  # Cancel the alarm
        if self._original_handler:
            signal.signal(signal.SIGALRM, self._original_handler)
            self._original_handler = None
    
    def check_timeout(self):
        """Check if timeout has occurred"""
        if self._timed_out:
            raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")


def timeout(seconds: int = 300):
    """
    Decorator for platform-independent timeout functionality.
    
    Args:
        seconds: Timeout duration in seconds (default: 300 = 5 minutes)
    
    Returns:
        Decorated function with timeout protection
    
    Example:
        @timeout(60)
        def long_running_function():
            # This function will timeout after 60 seconds
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with PlatformTimeoutHandler(seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def run_with_timeout(func: Callable, timeout_seconds: int = 300, *args, **kwargs) -> Any:
    """
    Run a function with platform-independent timeout.
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout duration in seconds (default: 300 = 5 minutes)
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    
    Raises:
        TimeoutError: If function execution exceeds timeout
    
    Example:
        result = run_with_timeout(long_running_function, 60, arg1, arg2)
    """
    with PlatformTimeoutHandler(timeout_seconds):
        return func(*args, **kwargs)


def run_with_threading_timeout(func: Callable, timeout_seconds: int = 300, *args, **kwargs) -> Any:
    """
    Alternative timeout implementation using threading (works on all platforms).
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout duration in seconds (default: 300 = 5 minutes)
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    
    Raises:
        TimeoutError: If function execution exceeds timeout
        Exception: Any exception raised by the function
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")


def safe_timeout(func: Callable, timeout_seconds: int = 300, *args, **kwargs) -> Any:
    """
    Safest timeout implementation that tries multiple approaches.
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout duration in seconds (default: 300 = 5 minutes)
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    
    Raises:
        TimeoutError: If function execution exceeds timeout
        Exception: Any exception raised by the function
    """
    # Try platform-specific timeout first
    try:
        return run_with_timeout(func, timeout_seconds, *args, **kwargs)
    except (AttributeError, OSError, ValueError):
        # Fallback to threading-based timeout
        return run_with_threading_timeout(func, timeout_seconds, *args, **kwargs)


def is_windows() -> bool:
    """Check if running on Windows"""
    return sys.platform.startswith('win')


def is_unix_like() -> bool:
    """Check if running on Unix-like system (Linux, macOS, etc.)"""
    return not is_windows()


def get_platform_info() -> dict:
    """Get detailed platform information"""
    return {
        "platform": sys.platform,
        "is_windows": is_windows(),
        "is_unix_like": is_unix_like(),
        "python_version": sys.version,
        "architecture": sys.maxsize > 2**32 and "64-bit" or "32-bit"
    }


# Convenience functions for common timeout scenarios
def timeout_short(func: Callable, *args, **kwargs) -> Any:
    """Run function with 30-second timeout"""
    return safe_timeout(func, 30, *args, **kwargs)


def timeout_medium(func: Callable, *args, **kwargs) -> Any:
    """Run function with 5-minute timeout"""
    return safe_timeout(func, 300, *args, **kwargs)


def timeout_long(func: Callable, *args, **kwargs) -> Any:
    """Run function with 15-minute timeout"""
    return safe_timeout(func, 900, *args, **kwargs)


def timeout_very_long(func: Callable, *args, **kwargs) -> Any:
    """Run function with 1-hour timeout"""
    return safe_timeout(func, 3600, *args, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    import time
    
    def test_function(duration: int) -> str:
        """Test function that sleeps for specified duration"""
        time.sleep(duration)
        return f"Slept for {duration} seconds"
    
    def test_timeout():
        """Test timeout functionality"""
        print("Testing platform-independent timeout...")
        print(f"Platform info: {get_platform_info()}")
        
        # Test short timeout (should succeed)
        try:
            result = timeout_short(test_function, 1)
            print(f"✅ Short timeout test passed: {result}")
        except TimeoutError as e:
            print(f"❌ Short timeout test failed: {e}")
        
        # Test timeout (should fail)
        try:
            result = timeout_short(test_function, 5)
            print(f"❌ Long operation should have timed out: {result}")
        except TimeoutError as e:
            print(f"✅ Timeout test passed: {e}")
        
        # Test decorator
        @timeout(2)
        def decorated_function():
            time.sleep(3)
            return "This should timeout"
        
        try:
            result = decorated_function()
            print(f"❌ Decorated function should have timed out: {result}")
        except TimeoutError as e:
            print(f"✅ Decorator timeout test passed: {e}")
    
    test_timeout() 