import numpy as np
import pytest

from conftest import SIZE_CASES
from math_class import MathClass

TOLERANCE = 1

pytestmark = pytest.mark.needs_steps("load", "crop")


def runSide(makePipeline, side, **kwargs):
    p = makePipeline(side, **kwargs)
    p.load()
    combined = p.scaleSource().getFrame().copy()
    sliceFrame = p.crop()
    return combined, sliceFrame.getFrame(), p.applyMask(sliceFrame).getFrame()


def putTogether(leftOut, rightOut, overlapPx, shift=0):
    resY, resX = leftOut.shape[:2]
    width = 2 * resX - overlapPx
    canvas = np.zeros((resY, width + 1, 3), np.int32)
    canvas[:, :resX] += leftOut
    start = resX - overlapPx + shift
    canvas[:, start:start + resX] += rightOut
    return canvas[:, :width]


@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_halves_fit_back_together(makePipeline, resX, resY, w, d, overlapPx):
    kw = dict(resXY=(resX, resY), w=w, d=d, gamma=1.0)
    combinedL, _, leftOut = runSide(makePipeline, "LEFT", **kw)
    combinedR, _, rightOut = runSide(makePipeline, "RIGHT", **kw)
    assert np.array_equal(combinedL, combinedR)

    result = putTogether(leftOut, rightOut, overlapPx)
    assert result.shape == combinedL.shape
    diff = np.abs(result - combinedL.astype(np.int32))
    assert diff.max() <= TOLERANCE
    assert diff[:, :resX - overlapPx].max() == 0
    assert diff[:, resX:].max() == 0


@pytest.mark.parametrize("shift", [-1, 1])
def test_test_notices_a_one_column_error(makePipeline, shift):
    kw = dict(resXY=(200, 60), d=89.5)
    combined, _, leftOut = runSide(makePipeline, "LEFT", **kw)
    _, _, rightOut = runSide(makePipeline, "RIGHT", **kw)
    overlapPx = MathClass.overlapPx(200, 100.0, 89.5)
    result = putTogether(leftOut, rightOut, overlapPx, shift=shift)
    assert np.abs(result - combined.astype(np.int32)).max() > TOLERANCE


@pytest.mark.parametrize("gamma", [0.5, 2.0, 3.0])
@pytest.mark.parametrize("side", ["LEFT", "RIGHT"])
def test_other_gamma_stays_in_range(makePipeline, side, gamma):
    _, sliceFrame, out = runSide(makePipeline, side, resXY=(200, 60), d=89.5, gamma=gamma)
    assert out.dtype == np.uint8 and out.shape == sliceFrame.shape
    assert np.all(out <= sliceFrame)
