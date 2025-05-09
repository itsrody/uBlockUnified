import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class UnifiedLogger:
    """Custom logger for the uBlock Unified List Generator."""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        """Initialize the logger.
        
        Args:
            name (str): Logger name
            log_file (Optional[str]): Path to log file. If None, logs to console only.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if log_file specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        """Log info level message."""
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        """Log error level message."""
        self.logger.error(message)
    
    def warning(self, message: str) -> None:
        """Log warning level message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log debug level message."""
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """Log critical level message."""
        self.logger.critical(message)
    
    def log_stats(self, stats: dict) -> None:
        """Log statistics about the list generation process.
        
        Args:
            stats (dict): Dictionary containing statistics to log.
        """
        self.info("=== List Generation Statistics ===")
        for key, value in stats.items():
            self.info(f"{key}: {value}")
        self.info("==============================")