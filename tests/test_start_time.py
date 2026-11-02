"""Shared start time: parseStartTime, PipelineClass.setStartAt/playVideo, main --start-at."""
import datetime
import time

import pytest

import main as mainModule
import pipeline_class
from pipeline_class import PipelineClass
from video_source import parseStartTime
from test_video import ScriptedDisplay, Q, fakeClock, frameNumber, videoPipeline, scripted  # noqa: F401

NOW = datetime.datetime(2026, 11, 5, 14, 0, 0)


# ---- parseStartTime ----

@pytest.mark.parametrize("text, expected", [
    ("14:30", datetime.datetime(2026, 11, 5, 14, 30, 0)),
    ("14:30:05", datetime.datetime(2026, 11, 5, 14, 30, 5)),
    ("  09:05:00 ", datetime.datetime(2026, 11, 5, 9, 5, 0)),
    ("2026-12-01 08:15", datetime.datetime(2026, 12, 1, 8, 15, 0)),
    ("2026-12-01 08:15:30", datetime.datetime(2026, 12, 1, 8, 15, 30)),
])
def test_parse_start_time(text, expected):
    assert parseStartTime(text, now=NOW) == expected.timestamp()


@pytest.mark.parametrize("bad", ["", "soon", "25:00", "14:61", "14", "2026-13-01 10:00", "14:30:05:01", None, 1430])
def test_bad_start_time_raises(bad):
    with pytest.raises(ValueError):
        parseStartTime(bad, now=NOW)


def test_a_time_that_has_passed_is_accepted():
    assert parseStartTime("08:00:00", now=NOW) < NOW.timestamp()


# ---- setStartAt ----

def test_set_start_at_accepts_numbers_and_none(makePipeline):
    p = makePipeline()
    p.setStartAt(1000)
    p.setStartAt(12.5)
    p.setStartAt(None)


@pytest.mark.parametrize("bad", ["14:30", True, float("nan"), float("inf"), [1]])
def test_set_start_at_rejects_other_values(makePipeline, bad):
    with pytest.raises(ValueError):
        makePipeline().setStartAt(bad)


# ---- playVideo with a shared start time ----

def test_shared_start_waits_without_a_key_and_starts_on_time(makeSettings, makeVideo, scripted):
    scripted.keys = [-1, -1, -1, Q]
    p = videoPipeline(makeSettings, makeVideo, frames=6, fps=10.0)
    p.setStartAt(100.0)
    # waiting: 99.0, 99.5, 100.0 (reached); then playing: 100.0 -> frame 0, 100.25 -> frame 2
    p.playVideo(clock=fakeClock([99.0, 99.5, 100.0, 100.0, 100.25]))
    display = scripted.instances[0]
    waits = [c[1] for c in display.calls if c[0] == "waitKey"]
    assert 0 not in waits                       # no "wait for a key without limit"
    numbers = [frameNumber(f[:, :100]) for f in display.shown()[1:]]
    assert numbers == [0, 2]


def test_a_computer_that_starts_late_joins_at_the_right_frame(makeSettings, makeVideo, scripted):
    scripted.keys = [Q]
    p = videoPipeline(makeSettings, makeVideo, frames=6, fps=10.0)
    p.setStartAt(100.0)
    p.playVideo(clock=fakeClock([100.0 + 0.43, 100.0 + 0.43]))    # 4.3 frames after the start
    shown = scripted.instances[0].shown()
    assert frameNumber(shown[-1][:, :100]) == 4


def test_late_start_loops_like_the_other_computer(makeSettings, makeVideo, scripted):
    scripted.keys = [Q]
    p = videoPipeline(makeSettings, makeVideo, frames=6, fps=10.0)
    p.setStartAt(100.0)
    p.playVideo(clock=fakeClock([100.0 + 2.35, 100.0 + 2.35]))    # 23 frames in: 23 % 6 = 5
    assert frameNumber(scripted.instances[0].shown()[-1][:, :100]) == 5


def test_quit_key_while_waiting_for_the_shared_start(makeSettings, makeVideo, scripted):
    scripted.keys = [Q]
    p = videoPipeline(makeSettings, makeVideo)
    p.setStartAt(1000.0)
    p.playVideo(clock=fakeClock([1.0]))
    display = scripted.instances[0]
    assert len(display.shown()) == 1 and display.calls[-1] == ("close",)


def test_default_clock_with_a_shared_start_is_the_wall_clock(makeSettings, makeVideo, scripted, monkeypatch):
    scripted.keys = [Q]
    p = videoPipeline(makeSettings, makeVideo)
    p.setStartAt(time.time() - 1.0)
    seen = []
    monkeypatch.setattr(pipeline_class.time, "time", lambda: (seen.append(1), 1e9 + 100)[1])
    p.setStartAt(1e9 + 99)
    p.playVideo()
    assert seen                                  # the wall clock was used, not the steady one


def test_without_a_shared_start_a_key_press_still_starts_the_video(makeSettings, makeVideo, scripted):
    scripted.keys = [13, Q]
    p = videoPipeline(makeSettings, makeVideo)
    p.playVideo(clock=fakeClock([0.0, 0.0]))
    assert [c for c in scripted.instances[0].calls if c[0] == "waitKey"][0][1] == 0


# ---- main.py ----

@pytest.fixture
def startCalls(monkeypatch):
    calls = []
    monkeypatch.setattr(PipelineClass, "run", lambda self: calls.append(self))
    return calls


def test_main_passes_the_start_time_to_a_video(makeSettings, makeVideo, startCalls):
    clip = makeVideo()
    path = makeSettings(sourcePath=clip)
    assert mainModule.main([path, "--start-at", "14:30:05"]) == 0
    assert startCalls[0]._PipelineClass__startAt == parseStartTime("14:30:05")


def test_main_without_start_at_leaves_it_empty(makeSettings, makeVideo, startCalls):
    assert mainModule.main([makeSettings(sourcePath=makeVideo())]) == 0
    assert startCalls[0]._PipelineClass__startAt is None


def test_main_ignores_start_at_for_a_picture_and_says_so(makeSettings, startCalls, caplog):
    assert mainModule.main([makeSettings(), "--start-at", "14:30"]) == 0
    assert startCalls[0]._PipelineClass__startAt is None
    assert "ignored" in caplog.text


def test_main_bad_start_time_is_a_usage_error(makeSettings, capsys):
    with pytest.raises(SystemExit) as excinfo:
        mainModule.main([makeSettings(), "--start-at", "soon"])
    assert excinfo.value.code == 2
    assert "Start time" in capsys.readouterr().err
