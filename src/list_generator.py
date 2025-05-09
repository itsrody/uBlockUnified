from typing import Dict, List, Optional, Set
import concurrent.futures
import json
from pathlib import Path
import requests
from datetime import datetime

from logger import UnifiedLogger
from error_handler import ErrorHandler, SourceError, ConfigError
from rule_optimizer import RuleOptimizer
from database import UBlockRuleConverter

class ListGenerator:
    """Generator for the unified uBlock Origin filter list."""
    
    def __init__(self, config_path: str = 'sources.json'):
        """Initialize the list generator.
        
        Args:
            config_path (str): Path to the configuration file.
        """
        self.config_path = Path(config_path)
        self.logger = UnifiedLogger("UnifiedList", "logs/unified_list.log")
        self.error_handler = ErrorHandler(self.logger)
        self.rule_optimizer = RuleOptimizer(self.logger, self.error_handler)
        self.rule_converter = UBlockRuleConverter()
        
        self.config = self._load_config()
        self.processed_rules: Set[str] = set()
    
    def _load_config(self) -> Dict:
        """Load and validate the configuration file.
        
        Returns:
            Dict: Validated configuration dictionary.
        
        Raises:
            ConfigError: If configuration is invalid or missing required fields.
        """
        try:
            if not self.config_path.exists():
                raise ConfigError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path) as f:
                config = json.load(f)
            
            # Validate required sections
            required_sections = ['metadata', 'settings', 'sources', 'sections']
            for section in required_sections:
                if section not in config:
                    raise ConfigError(f"Missing required section: {section}")
            
            return config
        except Exception as e:
            self.error_handler.handle_error(e, "config loading")
            raise
    
    @ErrorHandler.retry_on_error(max_retries=3, delay=5)
    def _fetch_source(self, source: Dict) -> Optional[List[str]]:
        """Fetch rules from a filter list source.
        
        Args:
            source (Dict): Source configuration dictionary.
        
        Returns:
            Optional[List[str]]: List of rules or None if fetch failed.
        """
        try:
            headers = {'User-Agent': self.config['settings']['user_agent']}
            response = requests.get(
                source['url'],
                headers=headers,
                timeout=self.config['settings']['timeout']
            )
            response.raise_for_status()
            
            rules = [
                line.strip()
                for line in response.text.splitlines()
                if line.strip() and not line.startswith(('!', '#'))
            ]
            
            self.logger.info(f"Fetched {len(rules)} rules from {source['name']}")
            return rules
            
        except Exception as e:
            raise SourceError(f"Failed to fetch {source['name']}: {str(e)}")
    
    def generate(self) -> bool:
        """Generate the unified filter list.
        
        Returns:
            bool: True if generation was successful, False otherwise.
        """
        try:
            # Reset counters
            self.error_handler.reset_counts()
            self.processed_rules.clear()
            
            all_rules: List[tuple] = []  # (rule, priority)
            
            # Fetch and process sources in parallel
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config['settings']['parallel_downloads']
            ) as executor:
                future_to_source = {
                    executor.submit(self._fetch_source, source): source
                    for source in self.config['sources']
                    if source['enabled']
                }
                
                for future in concurrent.futures.as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        rules = future.result()
                        if rules:
                            # Convert and optimize rules
                            for rule in rules:
                                converted_rule, status = self.rule_converter.convert_rule(
                                    rule, source['type']
                                )
                                if converted_rule:
                                    all_rules.append((converted_rule, source['priority']))
                    except Exception as e:
                        self.error_handler.handle_error(e, f"processing {source['name']}")
            
            # Sort rules by priority and optimize
            all_rules.sort(key=lambda x: x[1])
            unique_rules = [rule for rule, _ in all_rules]
            optimized_rules = self.rule_optimizer.optimize_rules(unique_rules)
            
            # Generate and write the final list
            self._write_list(optimized_rules)
            
            # Log statistics
            stats = {
                "Total sources processed": len(self.config['sources']),
                "Total rules processed": len(all_rules),
                "Unique rules": len(unique_rules),
                "Optimized rules": len(optimized_rules),
                "Errors encountered": self.error_handler.error_count,
                "Warnings encountered": self.error_handler.warning_count
            }
            self.logger.log_stats(stats)
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "list generation")
            return False
    
    def _write_list(self, rules: List[str]) -> None:
        """Write the generated rules to the output file.
        
        Args:
            rules (List[str]): List of optimized rules to write.
        """
        output_path = Path(self.config['settings']['output_file'])
        
        # Generate header
        header = self._generate_header(len(rules))
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(header)
            f.write('\n'.join(rules))
        
        self.logger.info(f"Written {len(rules)} rules to {output_path}")
    
    def _generate_header(self, rule_count: int) -> str:
        """Generate the metadata header for the unified list.
        
        Args:
            rule_count (int): Total number of rules in the list.
        
        Returns:
            str: Formatted header string.
        """
        meta = self.config['metadata']
        update_time = datetime.utcnow().strftime('%Y-%m-%d:%H:%M')
        
        header_lines = [
            "! Title: {}".format(meta['title']),
            "! Description: {}".format(meta['description']),
            "! Author: {}".format(meta['author']),
            "! Homepage: {}".format(meta['homepage']),
            "! Last Updated: {}".format(update_time),
            "! Total Rules: {}".format(rule_count),
            "! Expires: {}".format(meta['expires']),
            "!",
            "! This list is auto-generated by uBlock Unified List Generator",
            "! GitHub Repository: {}".format(meta['homepage']),
            "!",
            ""  # Empty line to separate header from rules
        ]
        
        return '\n'.join(header_lines)