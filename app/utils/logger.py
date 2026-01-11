import logging
import sys
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Creates a centralized logger with standard formatting.
    Output: Timestamp - Level - LoggerName - Message
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(level)
    
    # Console Handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

# Default app logger
app_logger = setup_logger("SalesBot")
