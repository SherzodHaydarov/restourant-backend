import logging
import logging.config
from app.core.config import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "audit": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "app": {"level": settings.LOG_LEVEL, "handlers": ["console", "file"]},
        "audit": {"level": "INFO", "handlers": ["audit"]},
        "sqlalchemy": {"level": "WARNING", "handlers": ["console"]},
    },
    "root": {"level": settings.LOG_LEVEL, "handlers": ["console", "file"]},
}


def setup_logging():
    """Setup application logging"""
    import os
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)


# Audit logger
def get_audit_logger():
    return logging.getLogger("audit")

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("app")
    logger.info("Logging configuration initialized successfully")