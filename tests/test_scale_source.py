"""PipelineClass.scaleSource tests (KAN-58)."""
import logging

import numpy as np
import pytest

from image import Image
from math_class import MathClass
from pipeline_class import PipelineClass
from side import Side


class StubSetup:
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
        return Side.LEFT


def make_pipeline(frame):
    p = PipelineClass(StubSetup())
    p._PipelineClass__setup = StubSetup()
    p._PipelineClass__math = MathClass
    if frame is not None:
        image = Image()
        image.setFrame(frame)
        frame = image
    p._PipelineClass__sourceFrame = frame
    return p


def test_scales_to_combined_width():
    # overlapPx = 384 -> 2 * 1920 - 384 = 3456
    p = make_pipeline(np.zeros((50, 100, 3), np.uint8))
    out = p.scaleSource()
    assert isinstance(out, Image)
    assert out.getShape() == (1080, 3456, 3)
    assert out.getFrame().dtype == np.uint8
    assert p._PipelineClass__sourceFrame is out


def test_shrinking_works():
    out = make_pipeline(np.zeros((2000, 6000, 3), np.uint8)).scaleSource()
    assert out.getShape() == (1080, 3456, 3)


def test_before_load_raises():
    with pytest.raises(ValueError):
        make_pipeline(None).scaleSource()


def test_other_aspect_ratio_is_cropped_not_stretched():
    # Left half black, right half white, much taller than the target: only the
    # vertical edges are cut, so the black/white split stays at the centre column.
    src = np.zeros((300, 100, 3), np.uint8)
    src[:, 50:] = 255
    out = make_pipeline(src).scaleSource()
    frame = out.getFrame()
    assert out.getShape() == (1080, 3456, 3)
    assert frame[:, 1700, 0].max() == 0 and frame[:, 1760, 0].min() == 255


def test_wide_source_is_cropped_at_the_sides():
    # Twice as wide as the target ratio: the middle part is kept.
    src = np.zeros((100, 640, 3), np.uint8)
    src[:, :160] = 255      # left quarter white, cut away
    src[:, 480:] = 255      # right quarter white, cut away
    frame = make_pipeline(src).scaleSource().getFrame()
    assert frame.shape == (1080, 3456, 3)
    assert frame[:, 10:-10].max() == 0


def test_matching_aspect_ratio_is_not_cropped(caplog):
    with caplog.at_level(logging.INFO):
        make_pipeline(np.zeros((1080, 3456, 3), np.uint8)).scaleSource()
    assert not caplog.records
