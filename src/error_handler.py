#!/usr/bin/env python3
"""
Error Handler for uBlock Unified List Generator

This module provides centralized error handling functionality
for the application, implementing graceful failure modes and
diagnostic information recording.

Author: Murtaza Salih (itsrody)
"""

import sys
import traceback
from typing import Optional, Any


class ErrorHandler:
    """Centralized error handling for the uBlock Unified List Generator."""
    
    def __init__(self, logger: Any):
        """
        Initialize the error handler.
        
        Args:
            logger: Logger instance for recording errors
        """
        self.logger = logger
        
    def handle(self, error: Exception, context: str = "", exit_code: Optional[int] = None) -> None:
        """
        Handle an exception with context information.
        
        Args:
            error: The exception to handle
            context: Context information about where the error occurred
            exit_code: If provided, exit the program with this code
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Format error message with context
        if context:
            message = f"{context}: {error_type} - {error_message}"
        else:
            message = f"{error_type} - {error_message}"
        
        # Log the error with stack trace
        self.logger.error(message)
        self.logger.debug(f"Stack trace:\n{traceback.format_exc()}")
        
        # Exit if requested
        if exit_code is not None:
            self.logger.critical(f"Exiting with code {exit_code} due to critical error")
            sys.exit(exit_code)
    
    def warn(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Warning message to log
        """
        self.logger.warning(message)
