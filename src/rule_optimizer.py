#!/usr/bin/env python3
"""
Rule Optimizer for uBlock Unified List Generator

This module handles optimization of validated rules including deduplication,
redundancy removal, and conflict resolution.

Author: Murtaza Salih (itsrody)
"""

from typing import List, Dict, Set
import re

class RuleOptimizer:
    """Optimizes validated rules for uBlock Origin compatibility."""
    
    def __init__(self, config: Any, error_handler: Any, logger: Any):
        self.config = config
        self.error_handler = error_handler
        self.logger = logger
        self.optimized_rules: Set[str] = set()

    def optimize(self, validated_rules: Dict[int, List[str]]) -> List[str]:
        """Main optimization pipeline."""
        self.logger.info("Starting optimization process")
        
        # Flatten rules while maintaining section order
        ordered_rules = self._order_rules_by_sections(validated_rules)
        
        # Optimization steps
        self._remove_duplicates(ordered_rules)
        self._remove_redundant_rules()
        self._resolve_conflicts()
        
        self.logger.info(f"Final optimized rules count: {len(self.optimized_rules)}")
        return sorted(self.optimized_rules, key=lambda x: (len(x.split('/')[0]), x))

    def _order_rules_by_sections(self, validated_rules: Dict[int, List[str]]) -> List[str]:
        """Order rules based on section priority from config."""
        ordered = []
        for section in self.config.sections:
            for rule_type in section["rule_types"]:
                if rule_type in validated_rules:
                    ordered.extend(validated_rules[rule_type])
        return ordered

    def _remove_duplicates(self, rules: List[str]) -> None:
        """Remove exact duplicates and similar matches."""
        seen = set()
        for rule in rules:
            if self._is_duplicate(rule, seen):
                continue
            seen.add(rule)
            self.optimized_rules.add(rule)
        self.logger.info(f"Removed {len(rules) - len(seen)} duplicates")

    def _is_duplicate(self, rule: str, seen: Set[str]) -> bool:
        """Check for various duplicate patterns."""
        base_rule = rule.split('$')[0]
        return any(base_rule == r.split('$')[0] for r in seen)

    def _remove_redundant_rules(self) -> None:
        """Remove rules made redundant by more general patterns."""
        domain_map = {}
        for rule in list(self.optimized_rules):
            if '##' in rule or '#@#' in rule:
                continue
            
            domain = rule.split('/')[0].lstrip('||').rstrip('^')
            if '*' in domain:
                continue
                
            if domain in domain_map:
                self.optimized_rules.discard(rule)
            else:
                domain_map[domain] = rule

    def _resolve_conflicts(self) -> None:
        """Handle conflicting exception and blocking rules."""
        blocking_rules = set()
        exception_rules = set()
        
        for rule in self.optimized_rules:
            if rule.startswith('@@'):
                exception_rules.add(rule[2:])
            else:
                blocking_rules.add(rule)
                
        # Remove exceptions that don't have matching blocks
        for exc in list(exception_rules):
            if exc not in blocking_rules:
                self.optimized_rules.discard(f'@@{exc}')
