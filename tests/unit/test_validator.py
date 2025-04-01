"""
Unit tests for the validator module.
"""
import unittest
from src.utils.validator import (
    is_valid_heart_rate,
    is_normal_heart_rate,
    is_low_heart_rate,
    is_high_heart_rate,
    MIN_HEART_RATE,
    MAX_HEART_RATE,
    ABSOLUTE_MIN_HEART_RATE,
    ABSOLUTE_MAX_HEART_RATE
)

class TestValidator(unittest.TestCase):
    """Test cases for the validator module."""

    def test_is_valid_heart_rate(self):
        """Test the is_valid_heart_rate function."""
        # Valid heart rates
        self.assertTrue(is_valid_heart_rate(60))
        self.assertTrue(is_valid_heart_rate(100))
        self.assertTrue(is_valid_heart_rate(MIN_HEART_RATE))
        self.assertTrue(is_valid_heart_rate(MAX_HEART_RATE))
        self.assertTrue(is_valid_heart_rate(ABSOLUTE_MIN_HEART_RATE))
        self.assertTrue(is_valid_heart_rate(ABSOLUTE_MAX_HEART_RATE))

        # Invalid heart rates
        self.assertFalse(is_valid_heart_rate(ABSOLUTE_MIN_HEART_RATE - 1))
        self.assertFalse(is_valid_heart_rate(ABSOLUTE_MAX_HEART_RATE + 1))
        self.assertFalse(is_valid_heart_rate(-10))
        self.assertFalse(is_valid_heart_rate(300))

        # Invalid types
        self.assertFalse(is_valid_heart_rate("60"))
        self.assertFalse(is_valid_heart_rate(None))
        self.assertFalse(is_valid_heart_rate([60]))

    def test_is_normal_heart_rate(self):
        """Test the is_normal_heart_rate function."""
        # Normal heart rates
        self.assertTrue(is_normal_heart_rate(60))
        self.assertTrue(is_normal_heart_rate(100))
        self.assertTrue(is_normal_heart_rate(MIN_HEART_RATE))
        self.assertTrue(is_normal_heart_rate(MAX_HEART_RATE))

        # Not normal heart rates
        self.assertFalse(is_normal_heart_rate(MIN_HEART_RATE - 1))
        self.assertFalse(is_normal_heart_rate(MAX_HEART_RATE + 1))
        self.assertFalse(is_normal_heart_rate(30))
        self.assertFalse(is_normal_heart_rate(200))

    def test_is_low_heart_rate(self):
        """Test the is_low_heart_rate function."""
        # Low heart rates
        self.assertTrue(is_low_heart_rate(MIN_HEART_RATE - 1))
        self.assertTrue(is_low_heart_rate(ABSOLUTE_MIN_HEART_RATE))

        # Not low heart rates
        self.assertFalse(is_low_heart_rate(MIN_HEART_RATE))
        self.assertFalse(is_low_heart_rate(MAX_HEART_RATE))
        self.assertFalse(is_low_heart_rate(ABSOLUTE_MIN_HEART_RATE - 1))
        self.assertFalse(is_low_heart_rate(100))

    def test_is_high_heart_rate(self):
        """Test the is_high_heart_rate function."""
        # High heart rates
        self.assertTrue(is_high_heart_rate(MAX_HEART_RATE + 1))
        self.assertTrue(is_high_heart_rate(ABSOLUTE_MAX_HEART_RATE))

        # Not high heart rates
        self.assertFalse(is_high_heart_rate(MIN_HEART_RATE))
        self.assertFalse(is_high_heart_rate(MAX_HEART_RATE))
        self.assertFalse(is_high_heart_rate(ABSOLUTE_MAX_HEART_RATE + 1))
        self.assertFalse(is_high_heart_rate(100))

if __name__ == '__main__':
    unittest.main()
