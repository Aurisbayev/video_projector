"""tools/preview_both.py tests."""
import os
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import preview_both
from math_class import MathClass


def test_joined_picture_matches_the_combined_source(makeSettings, tmp_path):
    left = makeSettings("LEFT", resXY=(200, 60), d=89.5)
    right = makeSettings("RIGHT", resXY=(200, 60), d=89.5)
    out = tmp_path / "joined.png"

    assert preview_both.main([left, right, "--save", str(out), "--no-window"]) == 0

    joined = cv2.imread(str(out))
    source = cv2.imread(str(tmp_path / "source.png"))
    overlapPx = MathClass.overlapPx(200, 100.0, 89.5)
    assert joined.shape == (60, 2 * 200 - overlapPx, 3)
    assert np.abs(joined.astype(np.int32) - source.astype(np.int32)).max() <= 1


def test_missing_settings_file_exits_1(tmp_path, capsys):
    code = preview_both.main([str(tmp_path / "a.json"), str(tmp_path / "b.json"), "--no-window"])
    assert code == 1
    assert "Cannot preview" in capsys.readouterr().err


def videoSettings(makeSettings, makeVideo, **kwargs):
    clip = makeVideo(frames=6, fps=10.0, size=(80, 30))
    return makeSettings("LEFT", resXY=(200, 60), d=80.0, sourcePath=clip, **kwargs)


def test_video_first_frame_is_saved_as_one_joined_picture(makeSettings, makeVideo, tmp_path):
    out = tmp_path / "first.png"
    path = videoSettings(makeSettings, makeVideo)
    assert preview_both.main([path, "--save", str(out), "--no-window"]) == 0
    joined = cv2.imread(str(out))
    assert joined.shape == (60, 2 * 200 - 40, 3)


def test_video_preview_keys_and_frames(makeSettings, makeVideo, monkeypatch):
    shown, keys = [], iter([-1, ord(" "), -1, ord(" "), -1, ord("q")])

    class FakeDisplay:
        def __init__(self, *a, **k): pass
        def show(self, frame): shown.append(frame)
        def waitKey(self, delayMs=0): return next(keys)
        def close(self): shown.append("closed")

    monkeypatch.setattr(preview_both, "Display", FakeDisplay)
    path = videoSettings(makeSettings, makeVideo)
    ticks = iter(float(i) / 10 for i in range(100))
    preview_both.playVideoPreview(path, window=True, clock=lambda: next(ticks))
    assert shown[-1] == "closed"
    frames = [f for f in shown if not isinstance(f, str)]
    assert len(frames) == 1 + 6
    assert all(f.shape == (60, 360, 3) for f in frames)


def test_video_with_two_settings_files_is_refused(makeSettings, makeVideo, capsys):
    path = videoSettings(makeSettings, makeVideo)
    assert preview_both.main([path, path, "--no-window"]) == 1
    assert "one settings file" in capsys.readouterr().err


# ---- projector gamma (adding light instead of pixel values) ----

def test_light_join_outside_the_overlap_is_exact():
    rng = np.random.default_rng(1)
    left = rng.integers(0, 256, (6, 20, 3), dtype=np.uint8)
    right = rng.integers(0, 256, (6, 20, 3), dtype=np.uint8)
    out = preview_both.join(left, right, 5, projectorGamma=2.2)
    assert out.shape == (6, 35, 3)
    assert np.array_equal(out[:, :15], left[:, :15])
    assert np.array_equal(out[:, 20:], right[:, 5:])


def test_light_join_of_two_halves_of_white_light_is_white():
    # Each side gives 0.5 of the light, so together they give full light.
    half = np.full((2, 4, 3), np.rint(255 * 0.5 ** (1 / 2.2)), np.uint8)
    out = preview_both.join(half, half, 4, projectorGamma=2.2)
    assert out.shape == (2, 4, 3)
    assert np.abs(out.astype(int) - 255).max() <= 1


def test_pixel_join_and_light_join_differ_in_the_overlap_only():
    left = np.full((2, 10, 3), 100, np.uint8)
    right = np.full((2, 10, 3), 100, np.uint8)
    pixel = preview_both.join(left, right, 4)
    light = preview_both.join(left, right, 4, projectorGamma=2.2)
    assert np.array_equal(pixel[:, :6], light[:, :6]) and np.array_equal(pixel[:, 10:], light[:, 10:])
    assert not np.array_equal(pixel[:, 6:10], light[:, 6:10])


def test_zero_overlap_light_join_just_places_the_pictures():
    left = np.full((2, 3, 3), 10, np.uint8)
    right = np.full((2, 3, 3), 200, np.uint8)
    out = preview_both.join(left, right, 0, projectorGamma=2.2)
    assert np.array_equal(out, np.concatenate([left, right], axis=1))


@pytest.mark.parametrize("bad", [0, -1.0])
def test_bad_projector_gamma_raises(bad):
    one = np.zeros((2, 4, 3), np.uint8)
    with pytest.raises(ValueError):
        preview_both.join(one, one, 2, projectorGamma=bad)


def seamDepth(makeSettings, tmp_path, gamma):
    """How much darker than a plain white picture the middle of the overlap is, in the light view."""
    path = makeSettings(resXY=(400, 20), d=80.0, gamma=gamma)
    cv2.imwrite(str(tmp_path / "source.png"), np.full((20, 720, 3), 255, np.uint8))
    out = tmp_path / ("seam%s.png" % gamma)
    assert preview_both.main([path, "--save", str(out), "--no-window", "--projector-gamma", "2.2"]) == 0
    row = cv2.imread(str(out))[10, :, 0].astype(int)
    return 255 - row.min()


def test_gamma_2_hides_the_seam_in_the_light_view_and_gamma_1_does_not(makeSettings, tmp_path):
    # The wall photos: gamma 1.0 shows a dark line, gamma 2.0 does not.
    assert seamDepth(makeSettings, tmp_path, 1.0) > 30
    assert seamDepth(makeSettings, tmp_path, 2.0) <= 8


def test_projector_gamma_flag_is_optional(makeSettings, tmp_path):
    path = makeSettings(resXY=(200, 60), d=89.5)
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    assert preview_both.main([path, "--save", str(a), "--no-window"]) == 0
    assert preview_both.main([path, "--save", str(b), "--no-window", "--projector-gamma", "2.2"]) == 0
    assert not np.array_equal(cv2.imread(str(a)), cv2.imread(str(b)))
