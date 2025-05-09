#!/usr/bin/env python3
"""
List Generator for uBlock Unified List Generator

This module handles the final list generation with proper formatting
and metadata headers.

Author: Murtaza Salih (itsrody)
"""

from datetime import datetime
import os
from typing import List

class ListGenerator:
    """Generates the final unified adblock list."""
    
    def __init__(self, config: Any, error_handler: Any, logger: Any):
        self.config = config
        self.error_handler = error_handler
        self.logger = logger
        self.stats = {
            'total_rules': 0,
            'sections': {},
            'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        }

    def generate(self, optimized_rules: List[str], output_path: str) -> None:
        """Generate the final output file."""
        self.logger.info(f"Generating unified list at {output_path}")
        
        header = self._generate_header(len(optimized_rules))
        sections = self._organize_rules(optimized_rules)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            for section_name, rules in sections.items():
                f.write(f"\n! {section_name}\n")
                f.write('\n'.join(rules))
                f.write('\n')
                
        self._update_statistics(sections)

    def _generate_header(self, rule_count: int) -> str:
        """Create the list header with metadata."""
        meta = self.config.metadata
        return f"""! Title: {meta['title']}
! Description: {meta['description']}
! Author: {meta['author']}
! Homepage: {meta['homepage']}
! Last updated: {self.stats['last_updated']}
! Total rules: {rule_count}
! Expires: {meta['expires']}
!
! Please report issues or contribute at:
! {meta['homepage']}
!
! ------------------------------ General Blocking Rules ------------------------------
"""

    def _organize_rules(self, rules: List[str]) -> Dict[str, List[str]]:
        """Organize rules by sections from config."""
        sections = {s['name']: [] for s in self.config.sections}
        
        for rule in rules:
            section = self.config.get_section_by_rule_type(
                self._classify_rule(rule)
            )
            if section:
                sections[section['name']].append(rule)
                
        return sections

    def _classify_rule(self, rule: str) -> int:
        """Simplified rule classification."""
        if '##' in rule: return 3
        if rule.startswith('@@'): return 4
        if '$removeparam=' in rule: return 14
        return 1

    def _update_statistics(self, sections: Dict[str, List[str]]) -> None:
        """Update statistics for reporting."""
        self.stats['total_rules'] = sum(len(r) for r in sections.values())
        for name, rules in sections.items():
            self.stats['sections'][name] = len(rules)

    def get_statistics(self) -> Dict[str, Any]:
        """Return generation statistics."""
        return self.stats
