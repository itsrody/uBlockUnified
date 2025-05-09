#!/usr/bin/env python3
"""
Rule Converter for uBlock Unified List Generator

This module validates and converts adblock rules from various sources
to ensure compatibility with uBlock Origin using a conversion database.

Author: Murtaza Salih (itsrody)
"""

import re
from typing import Dict, List, Any, Tuple, Optional, Set
from database import UBlockRuleConverter


class RuleConverter:
    """Validates and converts adblock rules to uBlock Origin syntax."""
    
    def __init__(self, config: Any, error_handler: Any, logger: Any):
        """
        Initialize the rule converter.
        
        Args:
            config: Configuration manager
            error_handler: Error handler for exceptions
            logger: Logger instance
        """
        self.config = config
        self.error_handler = error_handler
        self.logger = logger
        
        # Initialize the rule converter database
        try:
            self.db_converter = UBlockRuleConverter()
            self.logger.debug("Rule converter database initialized")
        except Exception as e:
            self.error_handler.handle(e, "Failed to initialize rule converter database")
            self.db_converter = None
    
    def process_rules(self, source_lists: Dict[str, Tuple[List[str], Dict[str, Any]]]) -> Dict[int, List[str]]:
        """
        Process rules from all sources, converting and validating them.
        
        Args:
            source_lists: Dictionary mapping source names to tuples of (rules list, source metadata)
            
        Returns:
            Dictionary mapping rule type IDs to lists of validated rules
        """
        validated_rules: Dict[int, List[str]] = {}
        processed_rules: Set[str] = set()  # Track all processed rules to avoid duplication
        
        # Initialize rule type lists
        for section in self.config.sections:
            for rule_type_id in section.get("rule_types", []):
                validated_rules[rule_type_id] = []
        
        # Process each source
        for source_name, (rules, source_metadata) in source_lists.items():
            source_type = source_metadata.get("type", "")
            self.logger.info(f"Processing {len(rules)} rules from {source_name} ({source_type})")
            
            for rule in rules:
                try:
                    # Skip empty rules or already processed rules
                    rule = rule.strip()
                    if not rule or rule in processed_rules:
                        continue
                    
                    # Convert rule to uBlock Origin syntax
                    converted_rule, status = self.convert_rule(rule, source_type)
                    if not converted_rule:
                        continue
                    
                    # Validate and classify the rule
                    rule_type_id = self.classify_rule(converted_rule)
                    if rule_type_id and rule_type_id in validated_rules:
                        validated_rules[rule_type_id].append(converted_rule)
                        processed_rules.add(converted_rule)
                    
                except Exception as e:
                    self.error_handler.warn(f"Error processing rule '{rule}': {str(e)}")
        
        # Log statistics
        total_rules = sum(len(rules) for rules in validated_rules.values())
        self.logger.info(f"Processed {len(processed_rules)} unique rules into {total_rules} validated rules")
        
        return validated_rules
    
    def convert_rule(self, rule: str, source_type: str) -> Tuple[str, str]:
        """
        Convert a rule to uBlock Origin syntax using the database.
        
        Args:
            rule: Original rule
            source_type: Type of the source (e.g., "AdBlock Plus", "AdGuard")
            
        Returns:
            Tuple of (converted rule, status message)
        """
        if not self.db_converter:
            return rule, "Database converter not available"
        
        try:
            return self.db_converter.convert_rule(rule, source_type)
        except Exception as e:
            self.error_handler.warn(f"Conversion error for rule '{rule}': {str(e)}")
            return "", "Conversion error"
    
    def classify_rule(self, rule: str) -> Optional[int]:
        """
        Classify a rule to determine its type.
        
        Args:
            rule: Rule to classify
            
        Returns:
            Rule type ID or None if rule is invalid or unsupported
        """
        # Basic URL blocking (type 1)
        if rule.startswith('||') and '^' in rule and not rule.startswith('@@'):
            return 1
        
        # Domain-specific blocking (type 2)
        if '##' not in rule and '$domain=' in rule:
            return 2
        
        # Element hiding rules (type 3)
        if '##' in rule and not rule.startswith('@@') and '#@#' not in rule and '#?#' not in rule:
            return 3
        
        # Exception rules (type 4)
        if rule.startswith('@@'):
            return 4
        
        # Regular expression rules (type 5)
        if rule.startswith('/') and rule.endswith('/'):
            return 5
        
        # Resource replacement rules (type 6)
        if '$redirect=' in rule:
            return 15
        
        # Scriptlet injection rules (type 7)
        if '##+js' in rule:
            return 7
        
        # HTML filtering rules (type 8)
        if '##^' in rule:
            return 8
        
        # Hosts file format rules (type 9)
        if re.match(r'^(0\.0\.0\.0|127\.0\.0\.1)\s+[a-z0-9.-]+$', rule):
            return 9
        
        # Extended CSS rules (type 11)
        if '##' in rule and (':has(' in rule or ':not(' in rule or ':is(' in rule):
            return 11
        
        # Network filter options (type 12)
        if '$' in rule and not '$redirect=' in rule and not '$domain=' in rule and not '$removeparam=' in rule:
            return 12
        
        # URL parameter removal rules (type 14)
        if '$removeparam=' in rule:
            return 14
        
        # Default to basic blocking if no specific type is matched
        if rule and not rule.startswith('!'):
            return 1
        
        # Invalid or unsupported rule
        return None