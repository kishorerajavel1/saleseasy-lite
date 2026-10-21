"""Only application decision metadata is logged; never requests or provider exception bodies."""

from logging.config import dictConfig


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"metadata": {"format": "%(message)s"}},
            "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "metadata"}},
            "loggers": {
                "saleseasy": {"handlers": ["console"], "level": "INFO", "propagate": False}
            },
        }
    )
