#!/usr/bin/env python3
"""
Configuration Manager for uBlock Unified List Generator

This module handles loading, validating, and providing access to
configuration settings defined in the sources.json file.

Author: Murtaza Salih (itsrody)
"""

import json
import os
from typing import Dict, List, Any, Optional, Union


class Config:
    """Configuration manager for the uBlock Unified List Generator."""

    def __init__(self, config_path: str, error_handler: Any):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
            error_handler: Error handler for handling exceptions
        """
        self.config_path = config_path
        self.error_handler = error_handler
        self.metadata: Dict[str, str] = {}
        self.settings: Dict[str, Any] = {}
        self.sources: List[Dict[str, Any]] = []
        self.sections: List[Dict[str, Any]] = []
        self.exclude_patterns: List[str] = []
        
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """Load configuration from the config file."""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Extract config sections
            self.metadata = config.get("metadata", {})
            self.settings = config.get("settings", {})
            self.sources = config.get("sources", [])
            self.sections = config.get("sections", [])
            self.exclude_patterns = config.get("exclude_patterns", [])
            
        except json.JSONDecodeError as e:
            self.error_handler.handle(e, f"Invalid JSON in configuration file: {self.config_path}")
        except Exception as e:
            self.error_handler.handle(e, f"Error loading configuration from {self.config_path}")
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        # Validate required metadata fields
        required_metadata = ["title", "description", "author"]
        for field in required_metadata:
            if field not in self.metadata:
                self.error_handler.warn(f"Missing required metadata field: {field}")
        
        # Validate required settings
        default_settings = {
            "cache_ttl": 86400,  # 24 hours
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 30,
            "user_agent": "uBlock-Unified-List-Generator/1.0",
            "parallel_downloads": 5,
            "output_file": "ublock-unified-list.txt"
        }
        
        # Apply defaults for missing settings
        for key, default_value in default_settings.items():
            if key not in self.settings:
                self.settings[key] = default_value
        
        # Validate sources
        if not self.sources:
            self.error_handler.handle(ValueError("No sources defined in configuration"))
        
        # Validate each source
        for i, source in enumerate(self.sources):
            required_source_fields = ["name", "type", "url", "enabled"]
            for field in required_source_fields:
                if field not in source:
                    self.error_handler.handle(
                        ValueError(f"Missing required field '{field}' in source #{i+1}: {source.get('name', 'Unknown')}")
                    )
            
            # Add default priority if missing
            if "priority" not in source:
                source["priority"] = i + 1
    
    def get_enabled_sources(self) -> List[Dict[str, Any]]:
        """
        Get list of enabled sources sorted by priority.
        
        Returns:
            List of enabled source configurations sorted by priority
        """
        enabled_sources = [s for s in self.sources if s.get("enabled", True)]
        return sorted(enabled_sources, key=lambda s: s.get("priority", 999))
    
    def get_section_by_rule_type(self, rule_type_id: int) -> Optional[Dict[str, Any]]:
        """
        Find the section that contains the specified rule type.
        
        Args:
            rule_type_id: ID of the rule type to find
            
        Returns:
            Section configuration or None if not found
        """
        for section in self.sections:
            if rule_type_id in section.get("rule_types", []):
                return section
        return None
    
    def get_source_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a source configuration by name.
        
        Args:
            name: Name of the source to find
            
        Returns:
            Source configuration or None if not found
        """
        for source in self.sources:
            if source.get("name") == name:
                return source
        return None
