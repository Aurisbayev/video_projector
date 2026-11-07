"""instant_run.py tests: no windows, no real show, no real clock."""
import datetime
import json
import os
import shlex
import subprocess
import sys

import pytest

import instant_run
from video_source import parseStartTime

NOW = datetime.datetime(2026, 11, 7, 14, 30, 0)


def fixedClock(moment=NOW):
    return lambda: moment


def parse(*argv, moment=NOW):
    return instant_run.parseArguments(list(argv), fixedClock(moment))


def commandFor(*argv, moment=NOW):
    args = parse(*argv, moment=moment)
    return instant_run.buildCommand(args, instant_run.resolveStartTime(args, fixedClock(moment)))


class Runner(object):
    """Stands in for runCommand: records each command and gives a chosen exit code."""

    def __init__(self, code=0, onRun=None):
        self.commands = []
        self.code = code
        self.onRun = onRun

    def __call__(self, command):
        self.commands.append(command)
        if self.onRun is not None:
            self.onRun(command)
        return self.code


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A fake repository root whose settings point at test_images/demo.mp4, already present."""
    (tmp_path / "test_images").mkdir()
    (tmp_path / "test_images" / "demo.mp4").write_bytes(b"video")
    with open(os.path.join(os.path.dirname(instant_run.__file__), "settings.video.json"),
              encoding="utf-8") as f:
        (tmp_path / "settings.video.json").write_text(f.read(), encoding="utf-8")
    monkeypatch.setattr(instant_run, "ROOT", str(tmp_path))
    return tmp_path


def runMain(*argv, run=None, moment=NOW, hasTkinter=lambda: True):
    run = Runner() if run is None else run
    code = instant_run.main(list(argv), run=run, now=fixedClock(moment), hasTkinter=hasTkinter)
    return code, run


def usageError(capsys, *argv):
    with pytest.raises(SystemExit) as e:
        runMain(*argv, run=Runner(onRun=lambda command: pytest.fail("something started")))
    assert e.value.code == 2
    return capsys.readouterr().err


# ---- command mapping ----

@pytest.mark.parametrize("flag,side", [("--left", "LEFT"), ("--right", "RIGHT")])
def test_side_runs_main_with_video_settings_and_start_time(flag, side):
    assert commandFor(flag) == [sys.executable, "main.py", "settings.video.json", "--side", side,
                                "--start-at", "2026-11-07 14:30:05"]


def test_left_video_is_the_same_as_left():
    assert commandFor("--left", "--video") == commandFor("--left")


@pytest.mark.parametrize("flag,side", [("--left", "LEFT"), ("--right", "RIGHT")])
def test_side_with_image_uses_picture_settings_and_no_start_time(flag, side):
    assert commandFor(flag, "--image") == [sys.executable, "main.py", "settings.json", "--side", side]


@pytest.mark.parametrize("argv,settings", [
    ((), "settings.video.json"),
    (("--video",), "settings.video.json"),
    (("--image",), "settings.json"),
])
def test_no_side_runs_the_preview(argv, settings):
    assert commandFor(*argv) == [sys.executable, os.path.join("tools", "preview_both.py"), settings,
                                 "--projector-gamma", "2.2"]


@pytest.mark.parametrize("argv,settings", [
    (("--gui",), "settings.video.json"),
    (("--gui", "--video"), "settings.video.json"),
    (("--gui", "--image"), "settings.json"),
])
def test_gui_opens_gui_py(argv, settings):
    assert commandFor(*argv) == [sys.executable, "gui.py", settings]


def test_the_programs_exist_in_the_repository():
    root = os.path.dirname(os.path.abspath(instant_run.__file__))
    for argv in (("--left",), (), ("--gui",), ("--image",)):
        command = commandFor(*argv)
        assert os.path.isfile(os.path.join(root, command[1]))
        assert os.path.isfile(os.path.join(root, command[2]))


def test_run_command_uses_the_repository_root_and_its_own_session(monkeypatch):
    seen = {}

    def fakeRun(command, **kwargs):
        seen.update(kwargs, command=command)
        return subprocess.CompletedProcess(command, 3)

    monkeypatch.setattr(instant_run.subprocess, "run", fakeRun)
    assert instant_run.runCommand(["x"]) == 3
    assert seen == {"command": ["x"], "cwd": instant_run.ROOT, "start_new_session": True}


def test_run_command_gives_a_shell_style_code_for_a_signal(monkeypatch):
    monkeypatch.setattr(instant_run.subprocess, "run",
                        lambda command, **kwargs: subprocess.CompletedProcess(command, -15))
    assert instant_run.runCommand(["x"]) == 143


def test_root_is_the_folder_of_the_script_not_the_current_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert os.path.isfile(os.path.join(instant_run.ROOT, "main.py"))


# ---- start time ----

def test_default_delay_is_the_named_constant(monkeypatch):
    assert instant_run.DEFAULT_START_DELAY_S == 5
    monkeypatch.setattr(instant_run, "DEFAULT_START_DELAY_S", 9)
    assert commandFor("--left")[-1] == "2026-11-07 14:30:09"


def test_start_in_adds_the_seconds():
    assert commandFor("--left", "--start-in", "30")[-1] == "2026-11-07 14:30:30"


def test_start_in_zero_is_not_the_default():
    assert commandFor("--left", "--start-in", "0")[-1] == "2026-11-07 14:30:00"


def test_start_in_rounds_a_fraction_up():
    assert commandFor("--left", "--start-in", "2.1")[-1] == "2026-11-07 14:30:03"


def test_start_in_rounds_a_clock_with_microseconds_up():
    moment = NOW.replace(microsecond=1)
    assert commandFor("--left", "--start-in", "5", moment=moment)[-1] == "2026-11-07 14:30:06"


def test_start_in_keeps_a_whole_second():
    moment = NOW.replace(microsecond=500000)
    assert commandFor("--left", "--start-in", "0.5", moment=moment)[-1] == "2026-11-07 14:30:01"


def test_start_in_across_midnight_has_the_next_date():
    moment = datetime.datetime(2026, 12, 31, 23, 59, 58, 500000)
    assert commandFor("--right", "--start-in", "5", moment=moment)[-1] == "2027-01-01 00:00:04"


def test_produced_time_parses_to_the_same_moment():
    text = commandFor("--left", "--start-in", "7")[-1]
    assert parseStartTime(text) == datetime.datetime(2026, 11, 7, 14, 30, 7).timestamp()


def test_produced_time_across_midnight_parses_on_the_next_day():
    moment = datetime.datetime(2026, 11, 7, 23, 59, 59)
    laterClock = datetime.datetime(2026, 11, 8, 0, 0, 1)
    text = commandFor("--left", moment=moment)[-1]
    assert parseStartTime(text, now=laterClock) == datetime.datetime(2026, 11, 8, 0, 0, 4).timestamp()


@pytest.mark.parametrize("value", ["14:30", "14:30:05", "2026-11-07 14:30", "2026-11-07 14:30:05"])
def test_start_at_is_passed_through(value):
    assert commandFor("--left", "--start-at", value)[-2:] == ["--start-at", value]


def test_start_at_spaces_are_dropped():
    assert commandFor("--left", "--start-at", " 14:30:05 ")[-1] == "14:30:05"


# ---- the second laptop ----

def laptopCommands(*argv, env):
    """Run the first laptop, then build what its printed command gives on the second one."""
    args = parse(*argv)
    start = instant_run.resolveStartTime(args, fixedClock())
    printed = instant_run.secondLaptopCommand(args.side, start, env)
    words = shlex.split(printed)
    position = words.index("instant_run.py")
    # The second laptop runs later: its clock must not matter.
    later = NOW + datetime.timedelta(minutes=1)
    secondArgs = parse(*words[position + 1:], moment=later)
    second = instant_run.buildCommand(secondArgs, instant_run.resolveStartTime(secondArgs, fixedClock(later)))
    return instant_run.buildCommand(args, start), second, words[:position]


@pytest.mark.parametrize("flag,other", [("--left", "RIGHT"), ("--right", "LEFT")])
def test_printed_command_gives_the_opposite_side_and_same_time(flag, other):
    first, second, _ = laptopCommands(flag, env={})
    assert second[3:5] == ["--side", other]
    assert second[1:3] == first[1:3]
    assert second[-2:] == first[-2:] == ["--start-at", "2026-11-07 14:30:05"]


def test_printed_command_keeps_a_given_start_at():
    first, second, _ = laptopCommands("--left", "--start-at", "2026-11-07 15:00", env={})
    assert second[-1] == first[-1] == "2026-11-07 15:00"


def test_printed_command_quotes_the_time():
    printed = instant_run.secondLaptopCommand("LEFT", "2026-11-07 14:30:05", {})
    assert printed == "python instant_run.py --right --start-at '2026-11-07 14:30:05'"


def test_printed_command_uses_uv_under_uv_run():
    assert laptopCommands("--left", env={"UV": "/bin/uv"})[2] == ["uv", "run", "python"]
    assert laptopCommands("--left", env={})[2] == ["python"]


def test_show_prints_time_second_laptop_clock_reminder_and_command(repo, capsys):
    code, run = runMain("--left")
    out = capsys.readouterr().out
    assert code == 0
    assert "starts at 2026-11-07 14:30:05" in out
    assert "instant_run.py --right --start-at '2026-11-07 14:30:05'" in out
    assert "same clock and time zone" in out and "automatic time" in out
    assert "Running: %s" % shlex.join(run.commands[0]) in out


def test_picture_prints_no_start_time(capsys):
    code, run = runMain("--left", "--image")
    out = capsys.readouterr().out
    assert code == 0 and "--start-at" not in out and "starts at" not in out
    assert "Running: %s" % shlex.join(run.commands[0]) in out


def test_preview_prints_no_second_laptop_command(repo, capsys):
    runMain()
    assert "second laptop" not in capsys.readouterr().out


# ---- usage errors ----

@pytest.mark.parametrize("argv", [
    ("--left", "--right"),
    ("--video", "--image"),
    ("--left", "--start-in", "5", "--start-at", "14:30"),
    ("--gui", "--left"),
    ("--gui", "--right"),
    ("--gui", "--start-in", "5"),
    ("--gui", "--start-in", "0"),
    ("--gui", "--start-at", "14:30"),
    ("--left", "--image", "--start-in", "5"),
    ("--left", "--image", "--start-in", "0"),
    ("--left", "--image", "--start-at", "14:30"),
    ("--left", "--image", "--start-at", ""),
    ("--image", "--start-in", "5"),
    ("--start-in", "5"),
    ("--start-in", "0"),
    ("--start-at", "14:30"),
    ("--left", "--start-at", "25:00"),
    ("--left", "--start-at", "soon"),
    ("--left", "--start-at", ""),
    ("--left", "--start-in", "-1"),
    ("--left", "--start-in", "-0.5"),
    ("--left", "--start-in", "-inf"),
    ("--left", "--start-in", "nan"),
    ("--left", "--start-in", "inf"),
    ("--left", "--start-in", "1e999"),
    ("--left", "--start-in", "1e300"),
    ("--left", "--start-in", "soon"),
    ("--left", "--start-i", "5"),
    ("settings.json",),
])
def test_usage_error_exits_2_and_starts_nothing(capsys, argv):
    usageError(capsys, *argv)


def test_usage_errors_say_what_is_wrong(capsys):
    assert "no start time" in usageError(capsys, "--left", "--image", "--start-in", "5")
    assert "--left or --right" in usageError(capsys, "--start-in", "5")
    assert "--gui cannot" in usageError(capsys, "--gui", "--left")
    assert "Start time must look like" in usageError(capsys, "--left", "--start-at", "25:00")
    assert "too large" in usageError(capsys, "--left", "--start-in", "1e300")


def test_bad_time_is_rejected_before_the_video_is_made(repo, capsys):
    (repo / "test_images" / "demo.mp4").unlink()
    usageError(capsys, "--left", "--start-at", "25:00")


# ---- the test video ----

def writeVideo(command):
    """Act like tools/make_test_video.py. Any other command must leave the disk alone."""
    if command[1].endswith("make_test_video.py"):
        with open(command[-1], "wb") as f:
            f.write(b"video")


@pytest.mark.parametrize("argv", [("--left",), (), ("--gui",)])
def test_missing_video_is_made_first_at_the_path_in_the_settings(repo, capsys, argv):
    video = repo / "test_images" / "demo.mp4"
    video.unlink()
    code, run = runMain(*argv, run=Runner(onRun=writeVideo))
    assert code == 0
    assert run.commands[0] == [sys.executable, os.path.join("tools", "make_test_video.py"), str(video)]
    assert run.commands[1] == commandFor(*argv)
    assert len(run.commands) == 2
    assert "is missing, making it first" in capsys.readouterr().out


def test_video_path_follows_the_settings_file(repo):
    settings = json.loads((repo / "settings.video.json").read_text(encoding="utf-8"))
    settings["sourcePath"] = "other.mp4"
    (repo / "settings.video.json").write_text(json.dumps(settings), encoding="utf-8")
    _, run = runMain("--left", run=Runner(onRun=writeVideo))
    assert run.commands[0][-1] == str(repo / "other.mp4")


def test_present_video_is_not_made_again(repo):
    _, run = runMain("--left")
    assert len(run.commands) == 1


def test_picture_never_makes_the_video(repo):
    (repo / "test_images" / "demo.mp4").unlink()
    code, run = runMain("--left", "--image")
    assert code == 0 and len(run.commands) == 1


def test_start_time_is_taken_after_the_video_is_made(repo):
    (repo / "test_images" / "demo.mp4").unlink()
    moments = [NOW]

    def slowGenerator(command):
        writeVideo(command)
        moments[0] = NOW + datetime.timedelta(seconds=60)

    run = Runner(onRun=slowGenerator)
    instant_run.main(["--left"], run=run, now=lambda: moments[0], hasTkinter=lambda: True)
    assert run.commands[1][-1] == "2026-11-07 14:31:05"


def test_generator_failure_stops_with_exit_1(repo, capsys):
    (repo / "test_images" / "demo.mp4").unlink()
    code, run = runMain("--left", run=Runner(code=7))
    assert code == 1
    assert len(run.commands) == 1
    assert "Cannot make the test video" in capsys.readouterr().err


def test_generator_success_without_a_file_stops_with_exit_1(repo, capsys):
    (repo / "test_images" / "demo.mp4").unlink()
    code, run = runMain("--left", run=Runner(code=0))
    assert code == 1 and len(run.commands) == 1
    assert "Cannot make the test video" in capsys.readouterr().err


def test_generator_failure_removes_a_half_written_video(repo):
    video = repo / "test_images" / "demo.mp4"
    video.unlink()
    runMain("--left", run=Runner(code=1, onRun=writeVideo))
    assert not video.exists()


def test_ctrl_c_in_the_generator_removes_a_half_written_video(repo):
    video = repo / "test_images" / "demo.mp4"
    video.unlink()

    def interrupted(command):
        writeVideo(command)
        raise KeyboardInterrupt

    code, _ = runMain("--left", run=Runner(onRun=interrupted))
    assert code == 130 and not video.exists()


def test_unreadable_settings_stops_with_exit_1(repo, capsys):
    (repo / "settings.video.json").write_text("{", encoding="utf-8")
    code, run = runMain("--left")
    assert code == 1 and run.commands == []
    assert "Cannot read settings.video.json" in capsys.readouterr().err


# ---- exit codes ----

@pytest.mark.parametrize("childCode", [0, 1, 2, 42])
@pytest.mark.parametrize("argv", [("--left",), (), ("--gui",), ("--right", "--image")])
def test_child_exit_code_is_passed_through(repo, argv, childCode):
    assert runMain(*argv, run=Runner(code=childCode))[0] == childCode


def test_ctrl_c_ends_cleanly(repo, capsys):
    def interrupted(command):
        raise KeyboardInterrupt

    code, _ = runMain("--left", run=Runner(onRun=interrupted))
    assert code == 130
    assert "Stopped." in capsys.readouterr().err


# ---- GUI and tkinter ----

def test_gui_with_tkinter_runs(repo):
    code, run = runMain("--gui", hasTkinter=lambda: True)
    assert code == 0 and run.commands == [commandFor("--gui")]


def test_gui_without_tkinter_explains_and_exits_1(repo, capsys):
    code, run = runMain("--gui", hasTkinter=lambda: False)
    err = capsys.readouterr().err
    assert code == 1 and run.commands == []
    assert "brew install python-tk@3.14" in err
    assert "sudo apt install python3-tk" in err


def test_gui_without_tkinter_does_not_make_the_video(repo):
    (repo / "test_images" / "demo.mp4").unlink()
    code, run = runMain("--gui", hasTkinter=lambda: False)
    assert code == 1 and run.commands == []


def test_tkinter_is_only_checked_for_the_gui(repo):
    code, run = runMain("--left", hasTkinter=lambda: pytest.fail("checked tkinter"))
    assert code == 0 and len(run.commands) == 1


def test_tkinter_available_when_the_import_works(monkeypatch):
    monkeypatch.setitem(sys.modules, "tkinter", object())
    assert instant_run.tkinterAvailable() is True


def test_tkinter_not_available_when_the_import_fails(monkeypatch):
    monkeypatch.setitem(sys.modules, "tkinter", None)
    assert instant_run.tkinterAvailable() is False
