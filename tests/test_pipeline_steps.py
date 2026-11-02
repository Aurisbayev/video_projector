import numpy as np
import pytest

from conftest import SIZE_CASES, asImage
from image import Image
from math_class import MathClass
from side import Side

SIDES = ["LEFT", "RIGHT"]


def overlapOf(p):
    setup = p._PipelineClass__setup
    return MathClass.overlapPx(setup.getProjectorResXY()[0], setup.getImageWidthCm(),
                               setup.getProjectorSpacingCm())


@pytest.mark.needs_steps("load")
def test_load_fills_source_frame_and_returns_it(makePipeline):
    p = makePipeline(sourceSize=(300, 50))
    frame = p.load()
    assert frame is p._PipelineClass__sourceFrame
    assert isinstance(frame, Image)
    assert frame.getFrame().dtype == np.uint8
    assert frame.getShape() == (50, 300, 3)


@pytest.mark.needs_steps("load")
def test_load_missing_file_raises_and_names_it(makePipeline, tmp_path):
    p = makePipeline()
    (tmp_path / "source.png").unlink()
    with pytest.raises(FileNotFoundError, match="source.png"):
        p.load()


@pytest.mark.needs_steps("load")
def test_load_file_that_is_not_a_picture_raises(makePipeline, tmp_path):
    p = makePipeline()
    (tmp_path / "source.png").write_text("this is not a picture")
    with pytest.raises(ValueError, match="source.png"):
        p.load()


@pytest.mark.needs_steps("load")
@pytest.mark.parametrize("side", SIDES)
@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_scale_source_gives_combined_size(makePipeline, side, resX, resY, w, d, overlapPx):
    p = makePipeline(side, resXY=(resX, resY), w=w, d=d, sourceSize=(97, 31))
    p.load()
    out = p.scaleSource()
    assert out.getShape() == (resY, 2 * resX - overlapPx, 3)
    assert out.getFrame().dtype == np.uint8
    assert p._PipelineClass__sourceFrame is out


@pytest.mark.needs_steps("load")
def test_scale_source_before_load_raises(makePipeline):
    with pytest.raises(ValueError):
        makePipeline().scaleSource()


@pytest.mark.needs_steps("load")
def test_both_sides_scale_to_the_same_picture(makePipeline):
    left, right = makePipeline("LEFT", sourceSize=(97, 31)), makePipeline("RIGHT", sourceSize=(97, 31))
    left.load()
    right.load()
    assert np.array_equal(left.scaleSource().getFrame(), right.scaleSource().getFrame())


@pytest.mark.needs_steps("load", "crop")
@pytest.mark.parametrize("side", SIDES)
@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_crop_size_and_position(makePipeline, side, resX, resY, w, d, overlapPx):
    p = makePipeline(side, resXY=(resX, resY), w=w, d=d)
    p.load()
    combined = p.scaleSource().getFrame().copy()
    sliceFrame = p.crop().getFrame()
    assert sliceFrame.shape == (resY, resX, 3)
    assert sliceFrame.dtype == np.uint8
    if side == "LEFT":
        assert np.array_equal(sliceFrame, combined[:, :resX])
    else:
        assert np.array_equal(sliceFrame, combined[:, -resX:])
    assert np.array_equal(p._PipelineClass__sourceFrame.getFrame(), combined)


@pytest.mark.needs_steps("load", "crop")
@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_slices_share_exactly_the_overlap(makePipeline, resX, resY, w, d, overlapPx):
    left, right = (makePipeline(s, resXY=(resX, resY), w=w, d=d) for s in SIDES)
    for p in (left, right):
        p.load()
        p.scaleSource()
    leftSlice, rightSlice = left.crop().getFrame(), right.crop().getFrame()
    assert np.array_equal(leftSlice[:, resX - overlapPx:], rightSlice[:, :overlapPx])
    assert not np.array_equal(leftSlice[:, resX - overlapPx - 1:], rightSlice[:, :overlapPx + 1])
    joined = np.concatenate([leftSlice, rightSlice[:, overlapPx:]], axis=1)
    assert np.array_equal(joined, left._PipelineClass__sourceFrame.getFrame())


@pytest.mark.needs_steps("crop")
def test_crop_before_load_raises(makePipeline):
    with pytest.raises(ValueError):
        makePipeline().crop()


@pytest.mark.needs_steps("load", "crop")
def test_crop_before_scale_raises_when_region_does_not_fit(makePipeline):
    p = makePipeline("RIGHT", sourceSize=(30, 10))
    p.load()
    with pytest.raises(ValueError):
        p.crop()


@pytest.mark.needs_steps("load", "crop")
@pytest.mark.parametrize("side", SIDES)
@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_apply_mask_changes_only_the_overlap(makePipeline, side, resX, resY, w, d, overlapPx):
    p = makePipeline(side, resXY=(resX, resY), w=w, d=d)
    p.load()
    p.scaleSource()
    sliceImage = p.crop()
    sliceFrame = sliceImage.getFrame()
    before = sliceFrame.copy()
    outImage = p.applyMask(sliceImage)
    out = outImage.getFrame()
    assert isinstance(outImage, Image)
    assert out.shape == before.shape and out.dtype == np.uint8
    assert np.array_equal(sliceFrame, before)
    assert outImage is not sliceImage
    if side == "LEFT":
        outside, inside = slice(0, resX - overlapPx), slice(resX - overlapPx, resX)
    else:
        outside, inside = slice(overlapPx, resX), slice(0, overlapPx)
    assert np.array_equal(out[:, outside], before[:, outside])
    assert np.all(out[:, inside] <= before[:, inside])
    assert not np.array_equal(out[:, inside], before[:, inside])


@pytest.mark.parametrize("side", SIDES)
def test_apply_mask_white_slice_becomes_alpha(makePipeline, side):
    p = makePipeline(side, resXY=(200, 60), d=89.5)
    alpha = np.array(p._PipelineClass__mask.getAlpha())
    out = p.applyMask(asImage(np.full((6, 200, 3), 255, np.uint8))).getFrame()
    expected = np.rint(alpha * 255).astype(np.uint8)
    assert np.array_equal(out, np.broadcast_to(expected[None, :, None], out.shape))


@pytest.mark.parametrize("width", [199, 201, 0])
def test_apply_mask_wrong_width_raises(makePipeline, width):
    p = makePipeline(resXY=(200, 60))
    with pytest.raises(ValueError):
        p.applyMask(asImage(np.zeros((6, width, 3), np.uint8)))
