from unittest import mock

import numpy as np
import pytest

from conftest import SIZE_CASES, asImage
from mask import Mask
from math_class import MathClass
from pipeline_class import PipelineClass
from region import Region
from setup_class import SetupClass
from side import Side


@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_constructor_gives_usable_object(makePipeline, loadSetup, makeSettings,
                                         resX, resY, w, d, overlapPx):
    setup = loadSetup(makeSettings(resXY=(resX, resY), w=w, d=d))
    p = PipelineClass(setup)
    assert p._PipelineClass__setup is setup
    assert p._PipelineClass__math is not None
    assert isinstance(p._PipelineClass__mask, Mask)
    assert isinstance(p._PipelineClass__region, Region)
    assert len(p._PipelineClass__mask.getAlpha()) == resX
    assert p._PipelineClass__sourceFrame is None
    assert p._PipelineClass__output is None


@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_region_and_mask_match_the_side(makePipeline, resX, resY, w, d, overlapPx):
    assert MathClass.overlapPx(resX, w, d) == overlapPx
    left = makePipeline("LEFT", resXY=(resX, resY), w=w, d=d)
    right = makePipeline("RIGHT", resXY=(resX, resY), w=w, d=d)

    region = left._PipelineClass__region
    assert (region.getXStartPx(), region.getWidthPx()) == (0, resX)
    region = right._PipelineClass__region
    assert (region.getXStartPx(), region.getWidthPx()) == (resX - overlapPx, resX)

    alphaLeft = np.array(left._PipelineClass__mask.getAlpha())
    alphaRight = np.array(right._PipelineClass__mask.getAlpha())
    assert np.all(alphaLeft[:resX - overlapPx] == 1.0)
    assert np.all(alphaRight[overlapPx:] == 1.0)
    assert np.all(alphaLeft[resX - overlapPx:] < 1.0)
    assert np.all(alphaRight[:overlapPx] < 1.0)


def test_mask_is_built_once(makeSettings, loadSetup):
    setup = loadSetup(makeSettings(side="RIGHT"))
    with mock.patch.object(MathClass, "blendMask", wraps=MathClass.blendMask) as spy:
        p = PipelineClass(setup)
        assert spy.call_count == 1
        maskAtStart = p._PipelineClass__mask
        sliceFrame = asImage(np.full((4, 200, 3), 200, np.uint8))
        for _ in range(3):
            p.applyMask(sliceFrame)
        assert spy.call_count == 1
        assert p._PipelineClass__mask is maskAtStart


def test_region_is_built_once(makeSettings, loadSetup):
    setup = loadSetup(makeSettings(side="RIGHT"))
    with mock.patch.object(MathClass, "cropRegion", wraps=MathClass.cropRegion) as spy:
        p = PipelineClass(setup)
        assert spy.call_count == 1
        assert p._PipelineClass__region is p._PipelineClass__region


def test_setup_is_not_loaded_again(makeSettings, loadSetup):
    setup = loadSetup(makeSettings())
    with mock.patch.object(SetupClass, "load") as load:
        PipelineClass(setup)
    assert load.call_count == 0


def test_both_sides_use_the_same_overlap(makePipeline):
    left = makePipeline("LEFT", resXY=(200, 60), d=89.5)
    right = makePipeline("RIGHT", resXY=(200, 60), d=89.5)
    overlapLeft = int((np.array(left._PipelineClass__mask.getAlpha()) < 1.0).sum())
    overlapRight = int((np.array(right._PipelineClass__mask.getAlpha()) < 1.0).sum())
    assert overlapLeft == overlapRight == 21


def test_setup_that_was_never_loaded_raises():
    with pytest.raises(ValueError, match="loaded"):
        PipelineClass(SetupClass())


def test_none_setup_raises():
    with pytest.raises(ValueError):
        PipelineClass(None)
