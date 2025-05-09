# uBlock Unified List Generator - Project Architecture

## Project Overview
The uBlock Unified List Generator is a Python application that fetches, validates, optimizes, and generates a unified adblock list fully compatible with uBlock Origin. The program processes multiple source lists, corrects their syntax using a conversion database, and outputs a well-formatted, optimized list.

## Core Components

### 1. Main Program (`main.py`)
- Entry point for the application
- Orchestrates the overall process flow
- Handles CLI arguments and configuration

### 2. Configuration Manager (`config.py`)
- Loads and validates the configuration from `sources.json`
- Provides access to configuration parameters

### 3. Source Fetcher (`source_fetcher.py`)
- Retrieves adblock lists from various sources (URLs, local files)
- Handles network requests, retries, and error handling
- Caches downloaded lists to reduce network traffic

### 4. Rule Converter (`rule_converter.py`)
- Interfaces with your existing `database.py` module
- Validates and converts rules to uBlock Origin syntax
- Applies syntax corrections based on source type

### 5. Rule Optimizer (`rule_optimizer.py`) 
- Removes duplicate and redundant rules
- Identifies and merges similar rules
- Handles rule priority and conflicts

### 6. List Generator (`list_generator.py`)
- Creates the final unified list
- Adds metadata and headers
- Formats the output according to adblock list standards

### 7. Logger (`logger.py`)
- Provides consistent logging across the application
- Configurable verbosity levels
- Outputs statistics about the process

### 8. Error Handler (`error_handler.py`)
- Centralizes error management
- Implements graceful failure modes
- Records diagnostic information

## Data Flow

```
[sources.json] → Configuration Manager → Source Fetcher → Raw Lists
Raw Lists → Rule Converter → Validated Rules
Validated Rules → Rule Optimizer → Optimized Rules
Optimized Rules → List Generator → Unified List
```

## GitHub Repository Structure

```
/
├── .github/
│   └── workflows/
│       └── update_list.yml    # GitHub Actions workflow
├── src/
│   ├── main.py                # Entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # Your existing database module
│   ├── source_fetcher.py      # Fetches source lists
│   ├── rule_converter.py      # Validates and converts rules
│   ├── rule_optimizer.py      # Optimizes and deduplicates rules
│   ├── list_generator.py      # Generates the final list
│   ├── logger.py              # Logging utilities 
│   └── error_handler.py       # Error handling
├── tests/                     # Unit and integration tests
├── output/                    # Generated lists directory
├── cache/                     # Cached source lists
├── sources.json               # Source list configuration
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
└── .gitignore                 # Git ignore file
```

## GitHub Actions Automation

A GitHub Actions workflow will be set up to:
1. Run the generator on a schedule (daily or weekly)
2. Update the unified list in the repository
3. Create a release with versioning
4. Deploy the list to GitHub Pages for easy access
