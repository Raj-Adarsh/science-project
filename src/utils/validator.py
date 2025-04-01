"""
Validator module for heart rate service.
Provides validation functions for heart rate data.
"""
import logging

logger = logging.getLogger(__name__)

# Heart rate ranges used in the original code
MIN_HEART_RATE = 50  # Below this triggers low heart rate alert
MAX_HEART_RATE = 150  # Above this triggers high heart rate alert

# Validation ranges
ABSOLUTE_MIN_HEART_RATE = 40  # Below this is invalid
ABSOLUTE_MAX_HEART_RATE = 180  # Above this is invalid

def is_valid_heart_rate(bpm):
    """
    Validates if a heart rate is within acceptable ranges.

    Args:
        bpm (int): Heart rate in beats per minute

    Returns:
        bool: True if heart rate is within valid range, False otherwise
    """
    if not isinstance(bpm, (int, float)):
        logger.warning(f"Heart rate must be a number, got {type(bpm).__name__}")
        return False

    if bpm < ABSOLUTE_MIN_HEART_RATE or bpm > ABSOLUTE_MAX_HEART_RATE:
        logger.warning(f"Heart rate outside valid range: {bpm}")
        return False

    return True

def is_normal_heart_rate(bpm):
    """
    Checks if a heart rate is within normal range (no alerts needed).

    Args:
        bpm (int): Heart rate in beats per minute

    Returns:
        bool: True if heart rate is within normal range, False otherwise
    """
    return MIN_HEART_RATE <= bpm <= MAX_HEART_RATE

def is_low_heart_rate(bpm):
    """
    Checks if a heart rate is considered low (bradycardia).

    Args:
        bpm (int): Heart rate in beats per minute

    Returns:
        bool: True if heart rate is considered low, False otherwise
    """
    return ABSOLUTE_MIN_HEART_RATE <= bpm < MIN_HEART_RATE

def is_high_heart_rate(bpm):
    """
    Checks if a heart rate is considered high (tachycardia).

    Args:
        bpm (int): Heart rate in beats per minute

    Returns:
        bool: True if heart rate is considered high, False otherwise
    """
    return MAX_HEART_RATE < bpm <= ABSOLUTE_MAX_HEART_RATE
