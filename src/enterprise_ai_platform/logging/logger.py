"""
Platform logger.
"""

from loguru import logger


def get_logger():
    """
    Return the shared platform logger.
    """

    return logger