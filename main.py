#!/usr/bin/env python3
"""
uBlock Unified List Generator
Main entry point for the application.

This script orchestrates the fetching, processing, conversion,
optimization, and generation of a unified adblock list optimized
for uBlock Origin.

Author: Murtaza Salih (itsrody)
"""

import os
import sys
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Import modules
from config import Config
from source_fetcher import SourceFetcher
from rule_converter import RuleConverter
from rule_optimizer import RuleOptimizer
from list_generator import ListGenerator
from logger import Logger
from error_handler import ErrorHandler


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a unified adblock list optimized for uBlock Origin."
    )
    parser.add_argument(
        "-c", "--config", 
        default="sources.json", 
        help="Path to the configuration file (default: sources.json)"
    )
    parser.add_argument(
        "-o", "--output", 
        default=None,
        help="Path to the output file (overrides config file setting)"
    )
    parser.add_argument(
        "--no-cache", 
        action="store_true", 
        help="Disable caching of source lists"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Print statistics after generation"
    )
    parser.add_argument(
        "--clean-cache", 
        action="store_true", 
        help="Clean the cache directory before running"
    )
    
    return parser.parse_args()


def setup_directories(dirs: List[str]) -> None:
    """Create necessary directories if they don't exist."""
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)


def main() -> int:
    """Main function to execute the unified list generation process."""
    start_time = time.time()
    
    # Parse arguments
    args = parse_arguments()
    
    # Set up logger
    log_level = Logger.DEBUG if args.verbose else Logger.INFO
    logger = Logger(level=log_level)
    logger.info("Starting uBlock Unified List Generator")
    
    # Set up error handler
    error_handler = ErrorHandler(logger)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = Config(args.config, error_handler)
        
        # Override output file if specified in arguments
        if args.output:
            config.settings["output_file"] = args.output
        
        # Set up directories
        setup_directories(["output", "cache"])
        
        # Clean cache if requested
        if args.clean_cache:
            logger.info("Cleaning cache directory")
            for file in os.listdir("cache"):
                if file.endswith(".txt"):
                    os.remove(os.path.join("cache", file))
        
        # Initialize components
        source_fetcher = SourceFetcher(
            config, 
            error_handler, 
            logger, 
            use_cache=not args.no_cache
        )
        rule_converter = RuleConverter(config, error_handler, logger)
        rule_optimizer = RuleOptimizer(config, error_handler, logger)
        list_generator = ListGenerator(config, error_handler, logger)
        
        # Process pipeline
        logger.info("Starting processing pipeline")
        
        # 1. Fetch sources
        logger.info("Fetching source lists")
        source_lists = source_fetcher.fetch_all_sources()
        logger.info(f"Fetched {len(source_lists)} source lists")
        
        # 2. Convert and validate rules
        logger.info("Converting and validating rules")
        validated_rules = rule_converter.process_rules(source_lists)
        logger.info(f"Validated {sum(len(rules) for rules in validated_rules.values())} rules")
        
        # 3. Optimize rules
        logger.info("Optimizing rules")
        optimized_rules = rule_optimizer.optimize(validated_rules)
        logger.info(f"Optimized to {len(optimized_rules)} rules")
        
        # 4. Generate unified list
        logger.info("Generating unified list")
        output_path = os.path.join("output", config.settings["output_file"])
        list_generator.generate(optimized_rules, output_path)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"Unified list generated successfully at {output_path}")
        logger.info(f"Execution completed in {execution_time:.2f} seconds")
        
        # Print statistics if requested
        if args.stats:
            stats = list_generator.get_statistics()
            logger.info("=== List Statistics ===")
            for key, value in stats.items():
                logger.info(f"{key}: {value}")
        
        return 0
        
    except Exception as e:
        error_handler.handle(e, "Fatal error in main execution")
        return 1


if __name__ == "__main__":
    sys.exit(main())