"""Logging setup for vkslab-esxi."""

import logging


def setup_logging(*, verbose: bool = False) -> logging.Logger:
    """Configure and return the package logger."""
    logger = logging.getLogger("vkslab_esxi")
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger
