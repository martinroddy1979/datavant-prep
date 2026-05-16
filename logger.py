# logger.py
import logging

import structlog


def configure_logger():
    """Configures the application to emit structured JSON logs for AWS CloudWatch."""
    structlog.configure(
        processors=[
            # Adds a precise timestamp to every log entry
            structlog.processors.TimeStamper(fmt="iso"),
            # Captures the severity level (INFO, WARNING, ERROR)
            structlog.processors.add_log_level,
            # Formats the output as a clean JSON string that cloud tools can parse
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger()

# Initialize a globally accessible logger instance for use throughout app
log = configure_logger()