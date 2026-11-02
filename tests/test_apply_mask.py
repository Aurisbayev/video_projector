"""PipelineClass.applyMask tests (D-19)."""
import numpy as np
import pytest

from image import Image
from math_class import MathClass
from pipeline_class import PipelineClass
from conftest import StubSetup
from side import Side


def wrap(frame):
    image = Image()
    image.setFrame(frame)
    return image


def make_pipeline(side, overlapPx=4, resX=10, gamma=1.0):
    p = PipelineClass(StubSetup())
    p._PipelineClass__mask = MathClass.blendMask(overlapPx, resX, side, gamma)
    return p


def test_columns_outside_overlap_unchanged():
    rng = np.random.default_rng(0)
    frame = rng.integers(0, 256, (5, 10, 3), dtype=np.uint8)
    left = make_pipeline(Side.LEFT).applyMask(wrap(frame)).getFrame()
    right = make_pipeline(Side.RIGHT).applyMask(wrap(frame)).getFrame()
    assert np.array_equal(left[:, :6], frame[:, :6])
    assert np.array_equal(right[:, 4:], frame[:, 4:])


def test_white_slice_becomes_mask_times_255():
    white = np.full((3, 10, 3), 255, np.uint8)
    out = make_pipeline(Side.LEFT).applyMask(wrap(white)).getFrame()
    alpha = np.array([1, 1, 1, 1, 1, 1, 0.875, 0.625, 0.375, 0.125])
    expected = np.rint(alpha * 255).astype(np.uint8)
    for row in range(3):
        for ch in range(3):
            assert np.array_equal(out[row, :, ch], expected)


def test_input_unchanged_and_new_array_returned():
    frame = np.full((2, 10, 3), 200, np.uint8)
    before = frame.copy()
    source = wrap(frame)
    result = make_pipeline(Side.RIGHT).applyMask(source)
    out = result.getFrame()
    assert isinstance(result, Image) and result is not source
    assert np.array_equal(frame, before)
    assert out is not frame
    assert out.dtype == np.uint8 and out.shape == frame.shape


def test_wrong_width_raises():
    with pytest.raises(ValueError):
        make_pipeline(Side.LEFT).applyMask(wrap(np.zeros((2, 9, 3), np.uint8)))


def test_no_mask_raises():
    with pytest.raises(ValueError):
        PipelineClass(StubSetup()).applyMask(wrap(np.zeros((2, 10, 3), np.uint8)))
