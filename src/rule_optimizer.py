import re
from typing import List, Set, Dict, Optional
from logger import UnifiedLogger
from error_handler import ErrorHandler, RuleError

class RuleOptimizer:
    """Optimizer for uBlock Origin filter rules."""
    
    def __init__(self, logger: UnifiedLogger, error_handler: ErrorHandler):
        """Initialize the rule optimizer.
        
        Args:
            logger (UnifiedLogger): Logger instance for optimization reporting.
            error_handler (ErrorHandler): Error handler for optimization errors.
        """
        self.logger = logger
        self.error_handler = error_handler
        self.optimized_rules: Set[str] = set()
        
        # Compile regex patterns for rule validation and optimization
        self.patterns = {
            'comment': re.compile(r'^!.*'),
            'empty': re.compile(r'^\s*$'),
            'invalid': re.compile(r'[^\x00-\x7F]'),  # Non-ASCII characters
            'whitespace': re.compile(r'\s+$'),  # Trailing whitespace
            'duplicate_caret': re.compile(r'\^+'),  # Multiple consecutive carets
            'duplicate_asterisk': re.compile(r'\*+'),  # Multiple consecutive asterisks
            'duplicate_separator': re.compile(r'[,\^]{2,}')  # Multiple separators
        }
    
    def optimize_rules(self, rules: List[str]) -> List[str]:
        """Optimize a list of filter rules for uBlock Origin.
        
        Args:
            rules (List[str]): List of rules to optimize.
        
        Returns:
            List[str]: Optimized rules list.
        """
        self.optimized_rules.clear()
        optimized: List[str] = []
        
        for rule in rules:
            try:
                if optimized_rule := self._optimize_rule(rule):
                    if optimized_rule not in self.optimized_rules:
                        optimized.append(optimized_rule)
                        self.optimized_rules.add(optimized_rule)
            except RuleError as e:
                self.error_handler.handle_warning(f"Rule optimization failed: {str(e)}")
        
        self.logger.info(f"Optimized {len(rules)} rules to {len(optimized)} unique rules")
        return optimized
    
    def _optimize_rule(self, rule: str) -> Optional[str]:
        """Optimize a single filter rule.
        
        Args:
            rule (str): Rule to optimize.
        
        Returns:
            Optional[str]: Optimized rule or None if rule should be discarded.
        """
        # Skip comments and empty lines
        if self.patterns['comment'].match(rule) or self.patterns['empty'].match(rule):
            return None
        
        # Check for invalid characters
        if self.patterns['invalid'].search(rule):
            raise RuleError(f"Rule contains invalid characters: {rule}")
        
        # Remove trailing whitespace
        rule = self.patterns['whitespace'].sub('', rule)
        
        # Optimize separators and wildcards
        rule = self.patterns['duplicate_caret'].sub('^', rule)
        rule = self.patterns['duplicate_asterisk'].sub('*', rule)
        rule = self.patterns['duplicate_separator'].sub(',', rule)
        
        # Optimize domain rules
        if rule.startswith('||'):
            rule = self._optimize_domain_rule(rule)
        
        # Optimize element hiding rules
        elif '##' in rule:
            rule = self._optimize_element_hiding_rule(rule)
        
        return rule if rule else None
    
    def _optimize_domain_rule(self, rule: str) -> str:
        """Optimize a domain-based filter rule.
        
        Args:
            rule (str): Domain rule to optimize.
        
        Returns:
            str: Optimized domain rule.
        """
        # Remove unnecessary wildcards after domain separator
        rule = re.sub(r'\|\|([^/]+)\*\.', r'||\1.', rule)
        
        # Optimize domain wildcards
        rule = re.sub(r'\*\.[a-z]', lambda m: m.group()[2:], rule)
        
        return rule
    
    def _optimize_element_hiding_rule(self, rule: str) -> str:
        """Optimize an element hiding rule.
        
        Args:
            rule (str): Element hiding rule to optimize.
        
        Returns:
            str: Optimized element hiding rule.
        """
        # Split domain and selector parts
        try:
            domains, selector = rule.split('##', 1)
        except ValueError:
            raise RuleError(f"Invalid element hiding rule format: {rule}")
        
        # Optimize selector
        selector = re.sub(r'\s*>\s*', '>', selector)  # Remove spaces around child combinator
        selector = re.sub(r'\s+', ' ', selector)  # Normalize whitespace
        selector = selector.strip()
        
        # Reconstruct rule
        return f"{domains}##{selector}" if domains else f"##{selector}"