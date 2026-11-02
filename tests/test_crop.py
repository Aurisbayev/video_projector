"""PipelineClass.crop tests (D-18)."""
import numpy as np
import pytest

from image import Image
from math_class import MathClass
from pipeline_class import PipelineClass
from side import Side


class StubSetup:
    def __init__(self, side):
        self._side = side

    def getProjectorResXY(self):
        return [1920, 1080]

    def getImageWidthCm(self):
        return 100.0

    def getProjectorSpacingCm(self):
        return 80.0

    def getBlendCurveGamma(self):
        return 1.0

    def getScaleMode(self):
        return "crop"

    def getProjectorSide(self):
        return self._side


def _image_from_array(array):
    image = Image()
    image.setFrame(array)
    return image


def make_pipeline(frame, side=Side.LEFT):
    p = PipelineClass(StubSetup(side))
    p._PipelineClass__setup = StubSetup(side)
    p._PipelineClass__math = MathClass
    p._PipelineClass__sourceFrame = _image_from_array(frame)
    return p


def test_left_slice_is_first_columns():
    resX, resY = 1920, 1080
    overlap = MathClass.overlapPx(resX, 100.0, 80.0)
    width = 2 * resX - overlap
    frame = np.zeros((resY, width, 3), np.uint8)
    frame[:, :, 0] = np.arange(width, dtype=np.uint8)  # unique column values

    out = make_pipeline(frame, Side.LEFT).crop()

    assert isinstance(out, Image)
    assert out.getFrame().shape == (resY, resX, 3)
    assert np.array_equal(out.getFrame()[:, :, 0], frame[:, :resX, 0])


def test_right_slice_is_last_columns():
    resX, resY = 1920, 1080
    overlap = MathClass.overlapPx(resX, 100.0, 80.0)
    width = 2 * resX - overlap
    frame = np.zeros((resY, width, 3), np.uint8)
    frame[:, :, 0] = np.arange(width, dtype=np.uint8)

    out = make_pipeline(frame, Side.RIGHT).crop()

    assert isinstance(out, Image)
    assert out.getFrame().shape == (resY, resX, 3)
    assert np.array_equal(out.getFrame()[:, :, 0], frame[:, -resX:, 0])


def test_slices_share_exactly_overlap_columns():
    resX, resY = 1920, 1080
    overlap = MathClass.overlapPx(resX, 100.0, 80.0)
    width = 2 * resX - overlap
    frame = np.random.default_rng(0).integers(0, 256, (resY, width, 3), dtype=np.uint8)

    left = make_pipeline(frame, Side.LEFT).crop().getFrame()
    right = make_pipeline(frame, Side.RIGHT).crop().getFrame()

    assert left.shape[1] == resX
    assert right.shape[1] == resX
    assert np.array_equal(left[:, -overlap:], right[:, :overlap])


def test_returns_copy_and_sourceframe_unchanged():
    resX, resY = 1920, 1080
    overlap = MathClass.overlapPx(resX, 100.0, 80.0)
    width = 2 * resX - overlap
    frame = np.full((resY, width, 3), 200, np.uint8)
    before = frame.copy()

    pipeline = make_pipeline(frame, Side.LEFT)
    out = pipeline.crop()
    out.getFrame()[:] = 0

    assert np.array_equal(pipeline._PipelineClass__sourceFrame.getFrame(), before)
    assert out is not pipeline._PipelineClass__sourceFrame


def test_no_frame_raises():
    p = PipelineClass(StubSetup(Side.LEFT))
    p._PipelineClass__setup = StubSetup(Side.LEFT)
    p._PipelineClass__math = MathClass
    p._PipelineClass__sourceFrame = None
    with pytest.raises(ValueError):
        p.crop()


def test_empty_image_frame_raises():
    p = PipelineClass(StubSetup(Side.LEFT))
    p._PipelineClass__setup = StubSetup(Side.LEFT)
    p._PipelineClass__math = MathClass
    p._PipelineClass__sourceFrame = Image()
    with pytest.raises(ValueError):
        p.crop()


def test_region_does_not_fit_raises():
    resX = 1920
    # Frame is too narrow for the full resX-wide slice.
    frame = np.zeros((1080, resX - 1, 3), np.uint8)
    with pytest.raises(ValueError):
        make_pipeline(frame, Side.LEFT).crop()
