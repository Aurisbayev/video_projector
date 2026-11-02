import logging
import os
import subprocess
import sys

import pytest

import main as mainModule
from pipeline_class import PipelineClass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def runCalls(monkeypatch):
    calls = []
    monkeypatch.setattr(PipelineClass, "run", lambda self: calls.append(self))
    return calls


def assertReadable(caplog, *words):
    text = caplog.text
    assert "Traceback" not in text
    assert all(r.exc_info is None for r in caplog.records)
    for word in words:
        assert word in text


def test_good_settings_exit_0_and_run_once(makeSettings, runCalls):
    assert mainModule.main([makeSettings()]) == 0
    assert len(runCalls) == 1
    assert isinstance(runCalls[0], PipelineClass)


def test_basicconfig_is_called_with_info(makeSettings, runCalls, monkeypatch):
    seen = []
    monkeypatch.setattr(logging, "basicConfig", lambda **kw: seen.append(kw))
    mainModule.main([makeSettings()])
    assert seen == [{"level": logging.INFO}]


def test_missing_file_exit_1(tmp_path, runCalls, caplog):
    assert mainModule.main([str(tmp_path / "nope.json")]) == 1
    assertReadable(caplog, "not found", "nope.json")
    assert runCalls == []


def test_broken_json_exit_1(tmp_path, runCalls, caplog):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    assert mainModule.main([str(bad)]) == 1
    assertReadable(caplog, "not valid JSON")
    assert runCalls == []


def test_missing_setting_exit_1(tmp_path, runCalls, caplog):
    bad = tmp_path / "bad.json"
    bad.write_text('{"projectorSide": "LEFT"}', encoding="utf-8")
    assert mainModule.main([str(bad)]) == 1
    assertReadable(caplog, "Missing setting")


def test_wrong_type_exit_1(makeSettings, runCalls, caplog):
    path = makeSettings()
    text = open(path, encoding="utf-8").read().replace("100.0", '"100"')
    open(path, "w", encoding="utf-8").write(text)
    assert mainModule.main([path]) == 1
    assertReadable(caplog, "imageWidthCm", "must be a number")


def test_folder_instead_of_file_exit_1(tmp_path, runCalls, caplog):
    assert mainModule.main([str(tmp_path)]) == 1
    assertReadable(caplog, "Cannot load settings")


def test_spacing_not_smaller_than_width_exit_2(makeSettings, runCalls, caplog):
    path = makeSettings(d=100.0, sourceSize=(10, 10))
    assert mainModule.main([path]) == 2
    assertReadable(caplog, "projectorSpacingCm", "smaller")
    assert runCalls == []


def test_gamma_out_of_range_exit_2(makeSettings, runCalls, caplog):
    assert mainModule.main([makeSettings(gamma=9.0)]) == 2
    assertReadable(caplog, "blendCurveGamma")
    assert runCalls == []


def test_source_picture_missing_exit_2(makeSettings, runCalls, caplog, tmp_path):
    path = makeSettings()
    os.remove(tmp_path / "source.png")
    assert mainModule.main([path]) == 2
    assertReadable(caplog, "Source image not found")
    assert runCalls == []


def test_pipeline_is_not_built_when_invalid(makeSettings, monkeypatch):
    def boom(setup):
        raise AssertionError("PipelineClass must not be created for invalid settings")
    monkeypatch.setattr(mainModule, "PipelineClass", boom)
    assert mainModule.main([makeSettings(d=150.0, sourceSize=(10, 10))]) == 2


def test_expected_error_in_run_exit_1_without_traceback(makeSettings, monkeypatch, caplog):
    def fail(self):
        raise ValueError("Failed to read image 'x.png'")
    monkeypatch.setattr(PipelineClass, "run", fail)
    assert mainModule.main([makeSettings()]) == 1
    assertReadable(caplog, "Failed to read image")


def cli(*args):
    return subprocess.run([sys.executable, "main.py", *args], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)


def test_cli_missing_file(tmp_path):
    r = cli(str(tmp_path / "nope.json"))
    assert r.returncode == 1
    assert "not found" in r.stderr and "Traceback" not in r.stderr


def test_cli_invalid_settings(makeSettings):
    r = cli(makeSettings(d=150.0, sourceSize=(10, 10)))
    assert r.returncode == 2
    assert "smaller" in r.stderr and "Traceback" not in r.stderr


def test_cli_without_argument_shows_usage():
    r = cli()
    assert r.returncode == 2
    assert "usage" in r.stderr.lower() and "Traceback" not in r.stderr


def test_side_option_overrides_the_file(makeSettings, runCalls):
    from side import Side
    path = makeSettings(side="LEFT")
    assert mainModule.main([path, "--side", "right"]) == 0
    assert runCalls[0]._PipelineClass__setup.getProjectorSide() is Side.RIGHT


def test_without_side_option_the_file_decides(makeSettings, runCalls):
    from side import Side
    assert mainModule.main([makeSettings(side="RIGHT")]) == 0
    assert runCalls[0]._PipelineClass__setup.getProjectorSide() is Side.RIGHT


def test_bad_side_value_is_rejected(makeSettings):
    with pytest.raises(SystemExit) as excinfo:
        mainModule.main([makeSettings(), "--side", "MIDDLE"])
    assert excinfo.value.code == 2
