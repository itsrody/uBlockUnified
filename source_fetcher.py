#!/usr/bin/env python3
"""
Source Fetcher for uBlock Unified List Generator

This module handles fetching adblock lists from various sources,
implementing caching, retries, and error handling.

Author: Murtaza Salih (itsrody)
"""

import os
import time
import hashlib
import requests
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class SourceFetcher:
    """Fetches adblock lists from various sources."""

    def __init__(self, config: Any, error_handler: Any, logger: Any, use_cache: bool = True):
        """
        Initialize the source fetcher.
        
        Args:
            config: Configuration manager
            error_handler: Error handler for exceptions
            logger: Logger instance
            use_cache: Whether to use cached lists
        """
        self.config = config
        self.error_handler = error_handler
        self.logger = logger
        self.use_cache = use_cache
        self.cache_dir = "cache"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.settings.get("user_agent", "uBlock-Unified-List-Generator/1.0")
        })
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def fetch_all_sources(self) -> Dict[str, Tuple[List[str], Dict[str, Any]]]:
        """
        Fetch all enabled source lists in parallel.
        
        Returns:
            Dictionary mapping source names to tuple of (rules list, source metadata)
        """
        sources = self.config.get_enabled_sources()
        self.logger.info(f"Starting fetch of {len(sources)} enabled sources")
        
        results = {}
        max_workers = min(len(sources), self.config.settings.get("parallel_downloads", 5))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks
            future_to_source = {
                executor.submit(self.fetch_source, source): source for source in sources
            }
            
            # Process completed tasks
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                source_name = source["name"]
                
                try:
                    rules = future.result()
                    if rules:
                        results[source_name] = (rules, source)
                        self.logger.info(f"Fetched {len(rules)} rules from {source_name}")
                    else:
                        self.logger.warning(f"No rules fetched from {source_name}")
                except Exception as e:
                    self.error_handler.handle(e, f"Error fetching {source_name}")
        
        return results
    
    def fetch_source(self, source: Dict[str, Any]) -> List[str]:
        """
        Fetch a single source list with retries and caching.
        
        Args:
            source: Source configuration
            
        Returns:
            List of rules from the source
        """
        source_name = source["name"]
        source_url = source["url"]
        self.logger.debug(f"Fetching source: {source_name} from {source_url}")
        
        # Check if we can use cached version
        cache_file = self._get_cache_file_path(source_name)
        if self.use_cache and self._is_cache_valid(cache_file):
            self.logger.debug(f"Using cached version of {source_name}")
            return self._load_from_cache(cache_file)
        
        # Fetch with retries
        max_retries = self.config.settings.get("max_retries", 3)
        retry_delay = self.config.settings.get("retry_delay", 5)
        timeout = self.config.settings.get("timeout", 30)
        
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.debug(f"Fetching {source_name} (attempt {attempt}/{max_retries})")
                response = self.session.get(source_url, timeout=timeout)
                response.raise_for_status()
                
                # Process the content
                content = response.text
                rules = self._process_source_content(content, source)
                
                # Cache the result
                if self.use_cache:
                    self._save_to_cache(cache_file, rules)
                
                return rules
                
            except requests.RequestException as e:
                if attempt == max_retries:
                    self.error_handler.warn(f"Failed to fetch {source_name} after {max_retries} attempts: {str(e)}")
                    # Try to use cached version even if expired
                    if self.use_cache and os.path.exists(cache_file):
                        self.logger.warning(f"Using expired cache for {source_name} due to fetch failure")
                        return self._load_from_cache(cache_file)
                    return []
                
                self.logger.debug(f"Retry {attempt}/{max_retries} for {source_name} in {retry_delay}s: {str(e)}")
                time.sleep(retry_delay)
        
        return []
    
    def _process_source_content(self, content: str, source: Dict[str, Any]) -> List[str]:
        """
        Process the raw content from a source.
        
        Args:
            content: Raw content from the source
            source: Source configuration
            
        Returns:
            List of processed rules
        """
        # Split content into lines
        lines = content.splitlines()
        
        # Filter out comments and empty lines based on exclude patterns
        exclude_patterns = self.config.exclude_patterns
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not any(self._matches_pattern(line, pattern) for pattern in exclude_patterns):
                filtered_lines.append(line)
        
        return filtered_lines
    
    def _matches_pattern(self, line: str, pattern: str) -> bool:
        """
        Check if a line matches an exclude pattern.
        
        Args:
            line: Line to check
            pattern: Regular expression pattern
            
        Returns:
            True if the line matches the pattern
        """
        import re
        return bool(re.match(pattern, line))
    
    def _get_cache_file_path(self, source_name: str) -> str:
        """
        Get the cache file path for a source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Path to the cache file
        """
        # Create a safe filename from source name
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in source_name)
        return os.path.join(self.cache_dir, f"{safe_name}.txt")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """
        Check if a cache file is valid and not expired.
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            True if the cache is valid
        """
        if not os.path.exists(cache_file):
            return False
        
        # Check if the cache is expired
        cache_ttl = self.config.settings.get("cache_ttl", 86400)  # Default: 24 hours
        file_mtime = os.path.getmtime(cache_file)
        current_time = time.time()
        
        return (current_time - file_mtime) < cache_ttl
    
    def _load_from_cache(self, cache_file: str) -> List[str]:
        """
        Load rules from a cache file.
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            List of rules from the cache
        """
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.error_handler.warn(f"Failed to load from cache {cache_file}: {str(e)}")
            return []
    
    def _save_to_cache(self, cache_file: str, rules: List[str]) -> None:
        """
        Save rules to a cache file.
        
        Args:
            cache_file: Path to the cache file
            rules: List of rules to save
        """
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                for rule in rules:
                    f.write(f"{rule}\n")
        except Exception as e:
            self.error_handler.warn(f"Failed to save to cache {cache_file}: {str(e)}")