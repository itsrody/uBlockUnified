#!/usr/bin/env python3

from list_generator import ListGenerator
from logger import UnifiedLogger

def main():
    """Main entry point for the uBlock Unified List Generator."""
    logger = UnifiedLogger("Main")
    
    try:
        logger.info("Starting uBlock Unified List Generator")
        
        generator = ListGenerator()
        if generator.generate():
            logger.info("List generation completed successfully")
            return 0
        else:
            logger.error("List generation failed")
            return 1
            
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())