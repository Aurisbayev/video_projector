
import pytest

from math_class import MathClass
from side import Side


@pytest.mark.parametrize("resX", [1280, 1920])
@pytest.mark.parametrize("w", [60, 100, 200, 300])
@pytest.mark.parametrize("ratio", [0.25, 0.5, 0.75, 0.8, 0.9])
def test_overlap_and_crop_regions(resX, w, ratio):
    d = w * ratio

    overlap = MathClass.overlapPx(resX, w, d)

    left = MathClass.cropRegion(Side.LEFT, resX, w, d)
    right = MathClass.cropRegion(Side.RIGHT, resX, w, d)

    left_start = left.getXStartPx()
    left_width = left.getWidthPx()
    right_start = right.getXStartPx()
    right_width = right.getWidthPx()

    # Overlap must be inside the projector resolution.
    assert 1 <= overlap < resX

    # LEFT starts at the beginning of the combined image.
    assert left_start == 0
    assert left_width == resX

    # RIGHT begins inside the LEFT image.
    assert right_start == resX - overlap
    assert right_width == resX

    # Both regions must cover the combined image without gaps.
    combined_width = 2 * resX - overlap

    left_columns = set(range(left_start, left_start + left_width))
    right_columns = set(range(right_start, right_start + right_width))

    assert left_columns | right_columns == set(range(combined_width))

    # The shared region must have exactly overlap columns.
    assert len(left_columns & right_columns) == overlap

    # Repeating the calculations must give identical results.
    assert MathClass.overlapPx(resX, w, d) == overlap


@pytest.mark.parametrize("resX", [1280, 1920])
@pytest.mark.parametrize("w", [100, 200])
def test_half_pixel_overlap(resX, w):
    # Choose a spacing that produces a half-pixel boundary.
    d = w * (1 - 100.5 / resX)

    overlap = MathClass.overlapPx(resX, w, d)

    assert 1 <= overlap < resX

    left = MathClass.cropRegion(Side.LEFT, resX, w, d)
    right = MathClass.cropRegion(Side.RIGHT, resX, w, d)

    assert left.getWidthPx() == resX
    assert right.getWidthPx() == resX
    assert right.getXStartPx() == resX - overlap


@pytest.mark.parametrize("resX", [1280, 1920])
@pytest.mark.parametrize("w", [60, 100, 200])
def test_invalid_projector_spacing(resX, w):
    for d in [w, w + 10]:
        with pytest.raises(ValueError):
            MathClass.overlapPx(resX, w, d)

        with pytest.raises(ValueError):
            MathClass.cropRegion(Side.LEFT, resX, w, d)

        with pytest.raises(ValueError):
            MathClass.cropRegion(Side.RIGHT, resX, w, d)
