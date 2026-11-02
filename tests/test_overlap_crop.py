"""MathClass.overlapPx / cropRegion tests (KAN-52)."""
import pytest

from math_class import MathClass
from side import Side


def test_overlap_px_basic():
    assert MathClass.overlapPx(1920, 100, 80) == 384


def test_overlap_px_rounds_down():
    assert MathClass.overlapPx(1920, 100, 83) == 326  # 326.4


def test_overlap_px_half_rounds_up():
    assert MathClass.overlapPx(1000, 100, 87.75) == 123  # 122.5


def test_overlap_px_returns_int():
    assert type(MathClass.overlapPx(1920, 100, 80)) is int


def test_crop_regions_basic():
    left = MathClass.cropRegion(Side.LEFT, 1920, 100, 80)
    right = MathClass.cropRegion(Side.RIGHT, 1920, 100, 80)
    assert (left.getXStartPx(), left.getWidthPx()) == (0, 1920)
    assert (right.getXStartPx(), right.getWidthPx()) == (1536, 1920)


@pytest.mark.parametrize("resX,w,d", [(1920, 100, 80), (1920, 100, 83), (1000, 100, 87.75), (1280, 120.5, 77.3)])
def test_crop_regions_no_gap_no_seam(resX, w, d):
    ov = MathClass.overlapPx(resX, w, d)
    left = MathClass.cropRegion(Side.LEFT, resX, w, d)
    right = MathClass.cropRegion(Side.RIGHT, resX, w, d)
    assert right.getXStartPx() + right.getWidthPx() == 2 * resX - ov
    assert left.getWidthPx() - right.getXStartPx() == ov


@pytest.mark.parametrize("d", [100, 120])
def test_d_not_smaller_than_w_raises(d):
    with pytest.raises(ValueError):
        MathClass.overlapPx(1920, 100, d)
    with pytest.raises(ValueError):
        MathClass.cropRegion(Side.LEFT, 1920, 100, d)


def test_invalid_side_raises():
    with pytest.raises(ValueError):
        MathClass.cropRegion(1, 1920, 100, 80)
    with pytest.raises(ValueError):
        MathClass.cropRegion("LEFT", 1920, 100, 80)
