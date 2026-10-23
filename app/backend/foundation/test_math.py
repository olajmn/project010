"""
Small, direct checks for math.py's four operations. Covers positive/negative/
decimal/zero operands and division by zero, not exhaustive coverage.
"""

# Contents
#  1. Basic arithmetic cases
#      - ADD_CASES
#      - SUBTRACT_CASES
#      - MULTIPLY_CASES
#      - DIVIDE_CASES
#
#  2. Division by zero

import pytest

from backend.foundation.math import add, divide, multiply, subtract

# 1. Basic arithmetic cases

# (a, b, expected)
ADD_CASES = (
    (2, 3, 5),
    (-2, -3, -5),
    (-5, 3, -2),
    (2.5, 0.5, 3.0),
    (0, 5, 5),
    (0, 0, 0),
)

SUBTRACT_CASES = (
    (5, 3, 2),
    (-5, -3, -2),
    (3, 5, -2),
    (2.5, 0.5, 2.0),
    (5, 0, 5),
    (0, 0, 0),
)

MULTIPLY_CASES = (
    (2, 3, 6),
    (-2, -3, 6),
    (-2, 3, -6),
    (2.5, 2, 5.0),
    (5, 0, 0),
    (0, 0, 0),
)

DIVIDE_CASES = (
    (6, 3, 2),
    (-6, -3, 2),
    (-6, 3, -2),
    (5, 2, 2.5),
    (0, 5, 0),
)


@pytest.mark.parametrize("a, b, expected", ADD_CASES)
def test_add(a, b, expected) -> None:
    assert add(a, b) == expected


@pytest.mark.parametrize("a, b, expected", SUBTRACT_CASES)
def test_subtract(a, b, expected) -> None:
    assert subtract(a, b) == expected


@pytest.mark.parametrize("a, b, expected", MULTIPLY_CASES)
def test_multiply(a, b, expected) -> None:
    assert multiply(a, b) == expected


@pytest.mark.parametrize("a, b, expected", DIVIDE_CASES)
def test_divide(a, b, expected) -> None:
    assert divide(a, b) == expected


# 2. Division by zero


# Positive, negative, and zero dividend - must always raise, never
# return 0/None/infinity.
@pytest.mark.parametrize("a", (5, -5, 0))
def test_divide_by_zero_raises(a) -> None:
    with pytest.raises(ZeroDivisionError):
        divide(a, 0)
