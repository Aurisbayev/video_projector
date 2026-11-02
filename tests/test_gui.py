"""gui.py tests: the engine without a window, and a short smoke run of the window."""
import json
import time

import cv2
import numpy as np
import pytest

import gui
from math_class import MathClass


def settingsFor(source, **changes):
    s = dict(gui.DEFAULT_SETTINGS, projectorResXY=[200, 60], imageWidthCm=100.0,
             projectorSpacingCm=80.0, blendCurveGamma=1.0, sourcePath=source)
    s.update(changes)
    return s


@pytest.fixture
def engine():
    e = gui.PreviewEngine()
    yield e
    e.close()


@pytest.fixture
def stillPath(makeSettings, tmp_path):
    makeSettings()                      # writes source.png
    return str(tmp_path / "source.png")


def test_still_picture_renders_the_joined_size(engine, stillPath):
    assert engine.apply(settingsFor(stillPath)) == []
    assert engine.isReady() and not engine.isVideo()
    assert engine.render().shape == (60, 2 * 200 - 40, 3)


def test_layout_uses_mathclass(engine, stillPath):
    engine.apply(settingsFor(stillPath, projectorSpacingCm=89.5))
    overlapCm, overlapPx, width = engine.getLayout()
    assert overlapCm == pytest.approx(10.5)
    assert overlapPx == MathClass.overlapPx(200, 100.0, 89.5)
    assert width == 2 * 200 - overlapPx


def test_single_sides_have_the_projector_size(engine, stillPath):
    engine.apply(settingsFor(stillPath))
    for view in ("left", "right"):
        assert engine.render(view=view).shape == (60, 200, 3)


def test_blend_off_leaves_the_overlap_unfaded(engine, stillPath):
    engine.apply(settingsFor(stillPath))
    on = engine.render(view="left", blend=True).astype(int)
    off = engine.render(view="left", blend=False).astype(int)
    assert np.array_equal(on[:, :160], off[:, :160])
    assert np.any(on[:, 160:] < off[:, 160:])


def test_guide_draws_the_overlap_edges_only_when_asked(engine, stillPath):
    engine.apply(settingsFor(stillPath))
    plain = engine.render(guide=False)
    marked = engine.render(guide=True)
    assert not np.array_equal(plain, marked)
    assert np.array_equal(plain, engine.render(guide=False))   # drawing must not change the pictures


def test_changing_gamma_changes_the_blend(engine, stillPath):
    engine.apply(settingsFor(stillPath, blendCurveGamma=1.0))
    one = engine.render(view="left")
    engine.apply(settingsFor(stillPath, blendCurveGamma=2.0))
    assert not np.array_equal(one, engine.render(view="left"))


def test_video_plays_by_frame_number(engine, makeVideo):
    clip = makeVideo(frames=6, fps=10.0, size=(80, 30))
    assert engine.apply(settingsFor(clip)) == []
    assert engine.isVideo() and engine.getFrameCount() == 6 and engine.getFps() == pytest.approx(10.0)
    grey = [float(np.mean(engine.render(i, view="left")[:, :100])) for i in range(6)]
    assert grey == sorted(grey) and grey[0] < grey[-1]
    assert engine.render(6).shape == engine.render(0).shape       # past the end loops


@pytest.mark.parametrize("change, word", [
    ({"projectorSpacingCm": 150.0}, "smaller"),
    ({"blendCurveGamma": 9.0}, "blendCurveGamma"),
    ({"sourcePath": "nope.png"}, "nope.png"),
    ({"sourcePath": ""}, "sourcePath"),
    ({"projectorResXY": [0, 60]}, "projectorResXY"),
])
def test_bad_settings_give_a_readable_problem(engine, stillPath, change, word):
    problems = engine.apply(settingsFor(stillPath, **change))
    assert len(problems) == 1 and word in problems[0]
    assert not engine.isReady()
    with pytest.raises(ValueError):
        engine.render()


def test_file_that_is_not_a_picture_is_a_problem(engine, tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_text("not a picture")
    problems = engine.apply(settingsFor(str(bad)))
    assert len(problems) == 1 and "bad.png" in problems[0]


def test_engine_recovers_after_a_problem(engine, stillPath):
    assert engine.apply(settingsFor(stillPath, projectorSpacingCm=150.0))
    assert engine.apply(settingsFor(stillPath)) == []
    assert engine.render().shape[0] == 60


def test_unknown_view_raises(engine, stillPath):
    engine.apply(settingsFor(stillPath))
    with pytest.raises(ValueError):
        engine.render(view="middle")


def test_load_settings_fills_defaults_and_ignores_extras(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"blendCurveGamma": 1.5, "extra": 1}))
    s = gui.loadSettings(str(path))
    assert s["blendCurveGamma"] == 1.5 and s["projectorResXY"] == [1920, 1080] and "extra" not in s


def test_load_settings_rejects_a_list(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("[1]")
    with pytest.raises(ValueError):
        gui.loadSettings(str(path))


def test_fit_into_keeps_the_proportions():
    out = gui.fitInto(np.zeros((100, 400, 3), np.uint8), 200, 200)
    assert out.shape == (50, 200, 3)


def test_window_smoke_run(makeSettings, tmp_path, monkeypatch):
    tkinter = pytest.importorskip("tkinter")
    path = makeSettings()
    data = json.loads(open(path).read())
    data["sourcePath"] = str(tmp_path / "source.png")
    open(path, "w").write(json.dumps(data))

    realMainloop = tkinter.Tk.mainloop

    def shortMainloop(self, n=0):
        # Run the real event loop for a moment, then stop it.
        self.after(600, self.quit)
        realMainloop(self)
        self.destroy()

    monkeypatch.setattr(tkinter.Tk, "mainloop", shortMainloop)
    try:
        assert gui.runApp([path]) == 0
    except tkinter.TclError as e:
        pytest.skip("no display for tkinter: %s" % e)


def test_light_view_changes_only_the_overlap_of_the_joined_picture(engine, stillPath):
    engine.apply(settingsFor(stillPath))
    pixel = engine.render()
    light = engine.render(projectorGamma=2.2)
    assert pixel.shape == light.shape
    assert np.array_equal(pixel[:, :160], light[:, :160]) and np.array_equal(pixel[:, 200:], light[:, 200:])
    assert not np.array_equal(pixel[:, 160:200], light[:, 160:200])


def test_light_view_does_not_change_a_single_side(engine, stillPath):
    engine.apply(settingsFor(stillPath))
    assert np.array_equal(engine.render(view="left"), engine.render(view="left", projectorGamma=2.2))


# ---- scale mode, paths and the start command ----

def test_engine_follows_the_scale_mode(engine, tmp_path):
    square = tmp_path / "square.png"
    cv2.imwrite(str(square), np.random.default_rng(3).integers(1, 256, (100, 100, 3), dtype=np.uint8))
    engine.apply(settingsFor(str(square), scaleMode="crop"))
    crop = engine.render(view="left")
    engine.apply(settingsFor(str(square), scaleMode="fit"))
    fit = engine.render(view="left")
    assert crop.shape == fit.shape and not np.array_equal(crop, fit)
    assert fit[:, :10].max() == 0                      # the black bar of the fitted square


def test_bad_scale_mode_is_a_problem(engine, stillPath):
    problems = engine.apply(settingsFor(stillPath, scaleMode="stretch"))
    assert len(problems) == 1 and "scaleMode" in problems[0]


def test_relative_source_path_is_found_from_the_current_folder(engine, stillPath, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert engine.apply(settingsFor("source.png")) == []
    assert engine.render().shape[0] == 60


def test_load_settings_makes_a_relative_path_relative_to_the_file(tmp_path):
    folder = tmp_path / "sub"
    folder.mkdir()
    (folder / "s.json").write_text(json.dumps({"sourcePath": "pic.png", "scaleMode": "fit"}))
    s = gui.loadSettings(str(folder / "s.json"))
    assert s["sourcePath"] == str(folder / "pic.png") and s["scaleMode"] == "fit"


def test_load_settings_defaults_the_scale_mode(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"sourcePath": "pic.png"}))
    assert gui.loadSettings(str(tmp_path / "s.json"))["scaleMode"] == "crop"


def test_relative_to_gives_a_short_path_when_it_can(tmp_path):
    assert gui.relativeTo(str(tmp_path / "a" / "x.png"), str(tmp_path)) == "a/x.png"


def test_start_command_without_a_start_time():
    command = gui.buildStartCommand("s.json", "RIGHT")
    assert command[-3:] == ["s.json", "--side", "RIGHT"] or command[2:5] == ["s.json", "--side", "RIGHT"]
    assert "--start-at" not in command and command[command.index("--side") + 1] == "RIGHT"


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_empty_start_time_means_a_key_press_start(empty):
    assert "--start-at" not in gui.buildStartCommand("s.json", "LEFT", empty)


def test_start_command_carries_the_start_time():
    command = gui.buildStartCommand("s.json", "LEFT", " 14:30:05 ")
    assert command[-2:] == ["--start-at", "14:30:05"]


def test_start_command_rejects_a_bad_time():
    with pytest.raises(ValueError):
        gui.buildStartCommand("s.json", "LEFT", "soon")
