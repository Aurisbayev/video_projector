"""tools/check_settings.py tests."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import check_settings


def test_one_valid_file(makeSettings, capsys):
    path = makeSettings()

    assert check_settings.main([path]) == 0
    assert capsys.readouterr().out == "OK: %s is valid.\n" % path


def test_one_invalid_file_exits_1(makeSettings, capsys):
    path = makeSettings(gamma=-1.0)

    assert check_settings.main([path]) == 1
    assert capsys.readouterr().out == "ERROR: %s is invalid.\n" % path


def test_file_that_is_not_json_exits_1(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")

    assert check_settings.main([str(path)]) == 1
    assert "not valid JSON" in capsys.readouterr().out


def test_missing_file_exits_1(tmp_path, capsys):
    assert check_settings.main([str(tmp_path / "none.json")]) == 1
    assert "not found" in capsys.readouterr().out


def test_second_file_invalid_exits_1(makeSettings, capsys):
    good = makeSettings(name="a.json")
    bad = makeSettings(gamma=-1.0, name="b.json")

    assert check_settings.main([good, bad]) == 1
    assert capsys.readouterr().out == "ERROR: %s is invalid.\n" % bad


def test_second_file_missing_exits_1(makeSettings, tmp_path, capsys):
    assert check_settings.main([makeSettings(), str(tmp_path / "none.json")]) == 1
    assert "not found" in capsys.readouterr().out


def test_matching_files_with_the_same_side(makeSettings, capsys):
    first = makeSettings("LEFT", name="a.json")
    second = makeSettings("LEFT", name="b.json")

    assert check_settings.main([first, second]) == 0
    out = capsys.readouterr().out
    assert "OK: Both settings files are valid and match." in out
    assert "projectorSide: LEFT / LEFT" in out


def test_matching_files_with_different_sides(makeSettings, capsys):
    first = makeSettings("LEFT", name="a.json")
    second = makeSettings("RIGHT", name="b.json")

    assert check_settings.main([first, second]) == 0
    out = capsys.readouterr().out
    assert "OK: Both settings files are valid and match." in out
    assert "projectorSide: LEFT / RIGHT" in out


@pytest.mark.parametrize("field, change", [
    ("projectorResXY", {"resXY": (300, 60)}),
    ("imageWidthCm", {"w": 120.0}),
    ("projectorSpacingCm", {"d": 70.0}),
    ("blendCurveGamma", {"gamma": 2.0}),
    ("sourcePath", {"sourcePath": "other.png"}),
])
def test_files_differing_in_a_shared_field_exit_1(makeSettings, tmp_path, capsys, field, change):
    (tmp_path / "other.png").touch()
    first = makeSettings(name="a.json")
    second = makeSettings(name="b.json", **change)

    assert check_settings.main([first, second]) == 1
    out = capsys.readouterr().out
    assert "ERROR: Settings do not match:" in out
    assert "  %s: first=" % field in out


def test_files_differing_only_in_scale_mode_exit_1(makeSettings, capsys):
    first = makeSettings(scaleMode="crop", name="a.json")
    second = makeSettings(scaleMode="fit", name="b.json")

    assert check_settings.main([first, second]) == 1
    assert "  scaleMode: first='crop', second='fit'" in capsys.readouterr().out
