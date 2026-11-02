"""Tests for MathClass overlapCm / totalWidthCm / pxPerCm (checked against hand-calculated values)."""
import pytest

from math_class import MathClass


class TestOverlapCm:
    def test_basic(self):
        # w=120, d=80 -> o = 120 - 80 = 40
        assert MathClass.overlapCm(120, 80) == pytest.approx(40.0)

    def test_float_inputs(self):
        # w=100.5, d=80 -> o = 20.5
        assert MathClass.overlapCm(100.5, 80) == pytest.approx(20.5)

    def test_no_overlap(self):
        # w == d -> no overlap
        assert MathClass.overlapCm(80, 80) == pytest.approx(0.0)

    def test_returns_float(self):
        assert isinstance(MathClass.overlapCm(120, 80), float)


class TestTotalWidthCm:
    def test_basic(self):
        # w=120, d=80 -> W = 120 + 80 = 200
        assert MathClass.totalWidthCm(120, 80) == pytest.approx(200.0)

    def test_float_inputs(self):
        # w=100.5, d=80 -> W = 180.5
        assert MathClass.totalWidthCm(100.5, 80) == pytest.approx(180.5)

    def test_returns_float(self):
        assert isinstance(MathClass.totalWidthCm(120, 80), float)

    def test_consistent_with_overlap(self):
        # W = 2w - o holds
        w, d = 120, 80
        assert MathClass.totalWidthCm(w, d) == pytest.approx(
            2 * w - MathClass.overlapCm(w, d)
        )


class TestPxPerCm:
    def test_divisible(self):
        # 1280 / 160 = 8
        assert MathClass.pxPerCm(1280, 160) == pytest.approx(8.0)

    def test_not_divisible(self):
        # 1280 / 120 = 10.666...
        assert MathClass.pxPerCm(1280, 120) == pytest.approx(32 / 3)

    def test_returns_float(self):
        assert isinstance(MathClass.pxPerCm(1280, 160), float)

    @pytest.mark.parametrize("w", [0, -10])
    def test_non_positive_width_raises(self, w):
        with pytest.raises(ValueError):
            MathClass.pxPerCm(1280, w)
