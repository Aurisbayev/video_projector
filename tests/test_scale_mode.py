"""scaleMode: crop (fill and cut the edges) and fit (the whole picture with black bars)."""
import json
import logging

import cv2
import numpy as np
import pytest

import main as mainModule
from conftest import SIZE_CASES
from pipeline_class import PipelineClass
from setup_class import SetupClass


def loadWith(makeSettings, mode, **kwargs):
    path = makeSettings(scaleMode=mode, **kwargs)
    setup = SetupClass()
    setup.load(path)
    return setup


# ---- SetupClass ----

def test_scale_mode_defaults_to_crop_when_the_file_has_none(makeSettings):
    setup = SetupClass()
    setup.load(makeSettings())
    assert setup.getScaleMode() == "crop" and setup.validate()


@pytest.mark.parametrize("text, expected", [("fit", "fit"), ("FIT", "fit"), (" Crop ", "crop")])
def test_scale_mode_is_read_from_the_file(makeSettings, text, expected):
    assert loadWith(makeSettings, text).getScaleMode() == expected


@pytest.mark.parametrize("bad", ["stretch", "", 3, None, True])
def test_bad_scale_mode_in_the_file_raises(makeSettings, bad):
    path = makeSettings()
    data = json.load(open(path))
    data["scaleMode"] = bad
    json.dump(data, open(path, "w"))
    with pytest.raises(ValueError, match="scaleMode"):
        SetupClass().load(path)


def test_set_scale_mode_overrides_and_rejects_bad_values(makeSettings):
    setup = loadWith(makeSettings, "crop")
    setup.setScaleMode("fit")
    assert setup.getScaleMode() == "fit"
    with pytest.raises(ValueError):
        setup.setScaleMode("stretch")
    assert setup.getScaleMode() == "fit"


# ---- scaleSource ----

def prepared(makePipeline, mode, side="LEFT", sourceSize=(100, 100), resXY=(200, 60), **kw):
    p = makePipeline(side, resXY=resXY, sourceSize=sourceSize, scaleMode=mode, **kw)
    p.load()
    return p


@pytest.mark.parametrize("mode", ["crop", "fit"])
@pytest.mark.parametrize("resX, resY, w, d, overlapPx", SIZE_CASES)
def test_both_modes_give_the_combined_size(makePipeline, mode, resX, resY, w, d, overlapPx):
    p = prepared(makePipeline, mode, resXY=(resX, resY), w=w, d=d, sourceSize=(97, 31))
    assert p.scaleSource().getShape() == (resY, 2 * resX - overlapPx, 3)


def test_fit_puts_a_square_picture_in_the_middle_with_black_side_bars(makePipeline):
    p = prepared(makePipeline, "fit", sourceSize=(100, 100))
    out = p.scaleSource().getFrame()
    height, width = out.shape[:2]                                  # 60 x 360
    columns = np.flatnonzero(out.max(axis=(0, 2)) > 0)
    assert columns[0] == (width - height) // 2 and columns[-1] == columns[0] + height - 1
    assert out[:, :columns[0]].max() == 0 and out[:, columns[-1] + 1:].max() == 0
    assert out[:, columns[0]:columns[-1] + 1].max() > 0


def test_fit_puts_a_very_wide_picture_in_the_middle_with_bars_above_and_below(makePipeline):
    p = prepared(makePipeline, "fit", sourceSize=(1200, 20))       # 60:1, the target is 6:1
    out = p.scaleSource().getFrame()
    rows = np.flatnonzero(out.max(axis=(1, 2)) > 0)
    assert out.shape[:2] == (60, 360)
    assert rows[0] > 0 and rows[-1] < 59                            # bars on both sides
    assert abs(rows[0] - (59 - rows[-1])) <= 1                      # centred
    assert out[:rows[0]].max() == 0 and out[rows[-1] + 1:].max() == 0


def test_crop_fills_every_column_while_fit_leaves_bars(makePipeline):
    fit = prepared(makePipeline, "fit", sourceSize=(100, 100)).scaleSource().getFrame()
    crop = prepared(makePipeline, "crop", sourceSize=(100, 100)).scaleSource().getFrame()
    assert (crop.max(axis=(0, 2)) > 0).all()          # the random test picture has no black column
    assert (fit.max(axis=(0, 2)) == 0).any()


def test_fit_is_the_same_as_crop_when_the_proportions_match(makePipeline):
    a = prepared(makePipeline, "fit", sourceSize=(360, 60)).scaleSource().getFrame()
    b = prepared(makePipeline, "crop", sourceSize=(360, 60)).scaleSource().getFrame()
    assert np.array_equal(a, b)


def test_fit_gives_the_same_picture_on_both_sides(makePipeline):
    left = prepared(makePipeline, "fit", "LEFT", sourceSize=(100, 100)).scaleSource().getFrame()
    right = prepared(makePipeline, "fit", "RIGHT", sourceSize=(100, 100)).scaleSource().getFrame()
    assert np.array_equal(left, right)


def test_fit_slices_still_share_exactly_the_overlap(makePipeline):
    pipes = {s: prepared(makePipeline, "fit", s, sourceSize=(100, 100)) for s in ("LEFT", "RIGHT")}
    for p in pipes.values():
        p.scaleSource()
    left, right = pipes["LEFT"].crop().getFrame(), pipes["RIGHT"].crop().getFrame()
    assert np.array_equal(left[:, 200 - 40:], right[:, :40])


def test_fit_notice_is_logged_once_per_source_size(makePipeline, caplog):
    p = prepared(makePipeline, "fit", sourceSize=(100, 100))
    with caplog.at_level(logging.INFO):
        p.scaleSource()
        p.load()
        p.scaleSource()
    messages = [r.getMessage() for r in caplog.records if "black bars" in r.getMessage()]
    assert len(messages) == 1


def test_fit_with_matching_proportions_logs_nothing(makePipeline, caplog):
    p = prepared(makePipeline, "fit", sourceSize=(360, 60))
    with caplog.at_level(logging.INFO):
        p.scaleSource()
    assert not caplog.records


def test_process_frame_in_fit_mode_leaves_the_bars_black(makePipeline):
    p = prepared(makePipeline, "fit", sourceSize=(100, 100))
    frame = np.full((100, 100, 3), 255, np.uint8)
    out = p.processFrame(frame, masked=False).getFrame()
    assert out[:, :10].max() == 0 and out[:, 10:].max() == 255      # LEFT slice: bars 0..129 of 360


# ---- main.py ----

@pytest.fixture
def runCalls(monkeypatch):
    calls = []
    monkeypatch.setattr(PipelineClass, "run", lambda self: calls.append(self))
    return calls


def test_main_scale_mode_option_overrides_the_file(makeSettings, runCalls):
    assert mainModule.main([makeSettings(scaleMode="crop"), "--scale-mode", "FIT"]) == 0
    assert runCalls[0]._PipelineClass__setup.getScaleMode() == "fit"


def test_main_without_the_option_the_file_decides(makeSettings, runCalls):
    assert mainModule.main([makeSettings(scaleMode="fit")]) == 0
    assert runCalls[0]._PipelineClass__setup.getScaleMode() == "fit"


def test_main_bad_scale_mode_option_is_rejected(makeSettings):
    with pytest.raises(SystemExit) as excinfo:
        mainModule.main([makeSettings(), "--scale-mode", "stretch"])
    assert excinfo.value.code == 2


def test_bad_scale_mode_in_the_file_exits_1(makeSettings, caplog):
    path = makeSettings()
    data = json.load(open(path))
    data["scaleMode"] = "stretch"
    json.dump(data, open(path, "w"))
    assert mainModule.main([path]) == 1
    assert "scaleMode" in caplog.text
