#!/usr/bin/env python3
"""
Logger for uBlock Unified List Generator

This module provides consistent logging functionality across
the application with configurable verbosity levels.

Author: Murtaza Salih (itsrody)
"""

import sys
import time
from datetime import datetime
from typing import Optional, TextIO


class Logger:
    """Logger with configurable verbosity levels."""
    
    # Log levels
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    
    # Level names for output
    LEVEL_NAMES = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        WARNING: "WARNING",
        ERROR: "ERROR",
        CRITICAL: "CRITICAL"
    }
    
    # ANSI color codes
    COLORS = {
        DEBUG: "\033[36m",  # Cyan
        INFO: "\033[32m",   # Green
        WARNING: "\033[33m", # Yellow
        ERROR: "\033[31m",  # Red
        CRITICAL: "\033[35m" # Purple
    }
    RESET = "\033[0m"
    
    def __init__(self, level: int = INFO, file: Optional[str] = None, 
                 use_colors: bool = True, timestamp: bool = True):
        """
        Initialize the logger.
        
        Args:
            level: Minimum log level to output
            file: Optional file path to write logs to
            use_colors: Whether to use colored output
            timestamp: Whether to include timestamps in log entries
        """
        self.level = level
        self.file_handle: Optional[TextIO] = None
        self.use_colors = use_colors and sys.stdout.isatty()
        self.timestamp = timestamp

        # Initialize file logging if specified
        if file:
            try:
                self.file_handle = open(file, 'a', encoding='utf-8')
            except Exception as e:
                self._write(f"Failed to open log file: {str(e)}", self.ERROR)
    
    def __del__(self):
        """Close file handle on destruction if opened."""
        if self.file_handle:
            try:
                self.file_handle.close()
            except:
                pass
    
    def _write(self, message: str, level: int) -> None:
        """
        Write a message to the console and/or log file.
        
        Args:
            message: Message to write
            level: Log level for the message
        """
        if level < self.level:
            return
        
        # Format the message
        level_name = self.LEVEL_NAMES.get(level, "UNKNOWN")
        
        # Add timestamp if enabled
        if self.timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted = f"[{timestamp}] [{level_name}] {message}"
        else:
            formatted = f"[{level_name}] {message}"
        
        # Console output with colors if enabled
        if self.use_colors and level in self.COLORS:
            color = self.COLORS[level]
            print(f"{color}{formatted}{self.RESET}")
        else:
            print(formatted)
        
        # Write to file if configured
        if self.file_handle:
            try:
                self.file_handle.write(formatted + "\n")
                self.file_handle.flush()
            except Exception as e:
                print(f"Error writing to log file: {str(e)}")
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._write(message, self.DEBUG)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self._write(message, self.INFO)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._write(message, self.WARNING)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self._write(message, self.ERROR)
    
    def critical(self, message: str) -> None:
        """Log a critical message."""
        self._write(message, self.CRITICAL)
