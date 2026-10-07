"""Tests for portion rounding utilities."""

import numpy as np
import pytest
from src.utils.portion_utils import round_portions


def test_nearest_rounding():
    """71.3g rounded to nearest 5g should be 70g."""
    result = round_portions(71.3, step=5)
    assert result == 70
    assert isinstance(result.item(), int)


def test_nearest_rounding_up():
    """337.6g rounded to nearest 5g should be 340g."""
    result = round_portions(337.6, step=5)
    assert result == 340


def test_nearest_boundary():
    """336.3g rounded to nearest 5g should be 335g."""
    result = round_portions(336.3, step=5)
    assert result == 335


def test_floor_mode():
    """337.6g floor rounded to 5g should be 335g."""
    result = round_portions(337.6, step=5, mode="floor")
    assert result == 335


def test_ceil_mode():
    """71.3g ceil rounded to 5g should be 75g."""
    result = round_portions(71.3, step=5, mode="ceil")
    assert result == 75


def test_array_batch():
    """Batch 1D array should be rounded correctly element-wise."""
    inputs = np.array([71.3, 336.3, 337.6])
    expected = np.array([70, 335, 340])
    result = round_portions(inputs, step=5)
    np.testing.assert_array_equal(result, expected)


def test_list_input():
    """Passing a Python list should convert and return rounded ndarray."""
    inputs = [71.3, 336.3, 337.6]
    expected = np.array([70, 335, 340])
    result = round_portions(inputs, step=5)
    np.testing.assert_array_equal(result, expected)


def test_2d_array():
    """2D array representing multi-meal portions."""
    inputs = np.array([
        [71.3, 336.3],
        [49.8, 102.1]
    ])
    expected = np.array([
        [70, 335],
        [50, 100]
    ])
    result = round_portions(inputs, step=5)
    np.testing.assert_array_equal(result, expected)


def test_custom_step():
    """Custom step sizes such as 10g."""
    result = round_portions(74.0, step=10)
    assert result == 70
    result_up = round_portions(76.0, step=10)
    assert result_up == 80


def test_invalid_parameters():
    """Invalid step and mode should raise ValueError."""
    with pytest.raises(ValueError, match="step must be a positive integer"):
        round_portions(100.0, step=0)

    with pytest.raises(ValueError, match="step must be a positive integer"):
        round_portions(100.0, step=-5)

    with pytest.raises(ValueError, match="Unknown mode"):
        round_portions(100.0, step=5, mode="invalid_mode")
