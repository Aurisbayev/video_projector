"""MathClass.blendMask tests (KAN-53)."""
import pytest

from math_class import MathClass
from side import Side


def alpha(side, overlap=4, resX=10, gamma=1.0):
    return MathClass.blendMask(overlap, resX, side, gamma).getAlpha()


def test_left_known_values():
    assert alpha(Side.LEFT) == pytest.approx([1, 1, 1, 1, 1, 1, 0.875, 0.625, 0.375, 0.125])


def test_right_known_values():
    assert alpha(Side.RIGHT) == pytest.approx([0.125, 0.375, 0.625, 0.875, 1, 1, 1, 1, 1, 1])


def test_gamma_one_overlap_sums_to_one():
    left = alpha(Side.LEFT, 384, 1920)[-384:]
    right = alpha(Side.RIGHT, 384, 1920)[:384]
    assert [a + b for a, b in zip(left, right)] == pytest.approx([1.0] * 384)


@pytest.mark.parametrize("gamma", [0.5, 1.0, 2.2, 3.0])
@pytest.mark.parametrize("side", [Side.LEFT, Side.RIGHT])
def test_range_length_monotonic(side, gamma):
    a = alpha(side, 384, 1920, gamma)
    assert len(a) == 1920
    assert all(0 <= v <= 1 for v in a)
    if side is Side.LEFT:
        ov = a[-384:]
        assert all(x >= y for x, y in zip(ov, ov[1:]))
    else:
        ov = a[:384]
        assert all(x <= y for x, y in zip(ov, ov[1:]))


def test_deterministic():
    assert alpha(Side.LEFT, 384, 1920, 2.2) == alpha(Side.LEFT, 384, 1920, 2.2)


@pytest.mark.parametrize("ov", [0, -1, 10, 11])
def test_bad_overlap_raises(ov):
    with pytest.raises(ValueError):
        MathClass.blendMask(ov, 10, Side.LEFT, 1.0)


@pytest.mark.parametrize("gamma", [0, -1.0])
def test_bad_gamma_raises(gamma):
    with pytest.raises(ValueError):
        MathClass.blendMask(4, 10, Side.LEFT, gamma)


def test_bad_side_raises():
    with pytest.raises(ValueError):
        MathClass.blendMask(4, 10, 1, 1.0)
