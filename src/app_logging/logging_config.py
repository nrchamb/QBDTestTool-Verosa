"""
Logging configuration for QBD Test Tool.

Defines log levels and provides utilities for log verbosity management.
"""

# Log level constants
LOG_MINIMAL = "MINIMAL"
LOG_NORMAL = "NORMAL"
LOG_VERBOSE = "VERBOSE"
LOG_DEBUG = "DEBUG"

# All available log levels (in order of verbosity)
LOG_LEVELS = [LOG_MINIMAL, LOG_NORMAL, LOG_VERBOSE, LOG_DEBUG]

# Log level hierarchy (higher number = more verbose)
LOG_LEVEL_PRIORITY = {
    LOG_MINIMAL: 0,
    LOG_NORMAL: 1,
    LOG_VERBOSE: 2,
    LOG_DEBUG: 3
}


def should_log(message_level: str, current_level: str) -> bool:
    """
    Determine if a message should be logged based on current log level.

    Args:
        message_level: The level of the message being logged
        current_level: The current configured log level

    Returns:
        True if message should be displayed, False otherwise
    """
    message_priority = LOG_LEVEL_PRIORITY.get(message_level, 1)  # Default to NORMAL
    current_priority = LOG_LEVEL_PRIORITY.get(current_level, 1)

    # Show message if its priority is <= current level priority
    return message_priority <= current_priority
