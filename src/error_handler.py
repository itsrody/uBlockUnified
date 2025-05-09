from typing import Any, Callable, Optional, Type, Union
from functools import wraps
import traceback
from logger import UnifiedLogger

class UnifiedError(Exception):
    """Base exception class for uBlock Unified List Generator."""
    pass

class SourceError(UnifiedError):
    """Exception raised for errors in source list processing."""
    pass

class RuleError(UnifiedError):
    """Exception raised for errors in rule processing."""
    pass

class ConfigError(UnifiedError):
    """Exception raised for configuration errors."""
    pass

class ErrorHandler:
    """Error handling utility for uBlock Unified List Generator."""
    
    def __init__(self, logger: UnifiedLogger):
        """Initialize the error handler.
        
        Args:
            logger (UnifiedLogger): Logger instance for error reporting.
        """
        self.logger = logger
        self._error_count = 0
        self._warning_count = 0
    
    @property
    def error_count(self) -> int:
        """Get the total number of errors encountered."""
        return self._error_count
    
    @property
    def warning_count(self) -> int:
        """Get the total number of warnings encountered."""
        return self._warning_count
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle an error by logging it and incrementing the error count.
        
        Args:
            error (Exception): The error to handle.
            context (str): Additional context about where the error occurred.
        """
        self._error_count += 1
        error_type = type(error).__name__
        error_msg = str(error)
        stack_trace = traceback.format_exc()
        
        self.logger.error(f"Error in {context}: {error_type} - {error_msg}")
        self.logger.debug(f"Stack trace:\n{stack_trace}")
    
    def handle_warning(self, message: str, context: str = "") -> None:
        """Handle a warning by logging it and incrementing the warning count.
        
        Args:
            message (str): The warning message.
            context (str): Additional context about where the warning occurred.
        """
        self._warning_count += 1
        self.logger.warning(f"Warning in {context}: {message}")
    
    @staticmethod
    def retry_on_error(
        max_retries: int = 3,
        retry_exceptions: tuple = (Exception,),
        delay: int = 1
    ) -> Callable:
        """Decorator to retry a function on specified exceptions.
        
        Args:
            max_retries (int): Maximum number of retry attempts.
            retry_exceptions (tuple): Tuple of exceptions to retry on.
            delay (int): Delay between retries in seconds.
        
        Returns:
            Callable: Decorated function with retry logic.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                import time
                
                attempts = 0
                while attempts < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except retry_exceptions as e:
                        attempts += 1
                        if attempts == max_retries:
                            raise
                        time.sleep(delay)
                return None
            return wrapper
        return decorator
    
    def reset_counts(self) -> None:
        """Reset error and warning counters."""
        self._error_count = 0
        self._warning_count = 0