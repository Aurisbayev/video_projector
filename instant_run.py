"""!
@brief One short command to show the test video or picture, on the projectors or as a preview.

It is a thin launcher: it chooses main.py, tools/preview_both.py or gui.py and their arguments, and runs that program from the repository root. All projection work stays in those programs.

Command-line options:
python instant_run.py [--left | --right] [--video | --image] [--start-in SECONDS | --start-at TIME] [--gui]

Options:
- --left, --right: Real show on this computer's projector. Without either, a preview on this computer.
- --video: Use settings.video.json. This is the default.
- --image: Use settings.json. A picture has no start time.
- --start-in SECONDS: Start the video in this many seconds. Default: DEFAULT_START_DELAY_S.
- --start-at TIME: Start the video at this shared time, in the same forms as main.py.
- --gui: Open gui.py instead. It cannot be combined with a side or a start time.

Exit codes:
- 0 or the code of the program that ran: that program's own result
- 1: The test video could not be made, the settings file could not be read, or tkinter is missing for --gui
- 2: A wrong command-line option
- 130: Stopped with Ctrl-C
"""


import argparse
import datetime
import math
import os
import shlex
import subprocess
import sys

from setup_class import SetupClass
from video_source import parseStartTime

## Repository root. Every program runs from here, so the launcher works from any folder.
ROOT = os.path.dirname(os.path.abspath(__file__))
## Settings file for the test video, relative to ROOT.
VIDEO_SETTINGS = "settings.video.json"
## Settings file for the test picture, relative to ROOT.
IMAGE_SETTINGS = "settings.json"
## Time between the command and the video start if none is given, so the window can open [s].
DEFAULT_START_DELAY_S = 5
## Projector gamma for the preview, as text for its command line [none].
PREVIEW_PROJECTOR_GAMMA = "2.2"
## Form of a computed start time. It has the date, so it still works across midnight.
START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
## Exit code 1: the launcher could not prepare the program.
EXIT_ERROR = 1
## Exit code after Ctrl-C, the shell's usual 128 + SIGINT.
EXIT_INTERRUPTED = 130
## Shown if tkinter cannot be imported.
TKINTER_HELP = ("gui.py needs tkinter, and this Python cannot import it.\n"
                "Homebrew Python: brew install python-tk@3.14\n"
                "Debian or Ubuntu: sudo apt install python3-tk")


def parseStartDelay(text):
    """!
    @brief Reads the value of --start-in.

    @param text The text after --start-in [s].
    @return [float] The delay [s].
    @throws argparse.ArgumentTypeError If the text is not a finite number, or is negative.
    """
    try:
        seconds = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("%r is not a number of seconds" % text)
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError("must be a finite number, 0 or more, got %r" % text)
    return seconds


def buildParser():
    """!
    @brief Creates the command-line parser.

    @return [argparse.ArgumentParser] The parser, with only the rules argparse can check by itself.
    """
    parser = argparse.ArgumentParser(
        description="Show the test video or picture on the projectors, or as a preview "
                    "on this computer if no side is given.",
        allow_abbrev=False)
    side = parser.add_mutually_exclusive_group()
    side.add_argument("--left", dest="side", action="store_const", const="LEFT",
                      help="real show: this computer drives the left projector")
    side.add_argument("--right", dest="side", action="store_const", const="RIGHT",
                      help="real show: this computer drives the right projector")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--video", action="store_true",
                        help="use %s (the default)" % VIDEO_SETTINGS)
    source.add_argument("--image", action="store_true", help="use %s" % IMAGE_SETTINGS)
    start = parser.add_mutually_exclusive_group()
    start.add_argument("--start-in", type=parseStartDelay, metavar="SECONDS",
                       help="start the video in this many seconds (default %d)"
                            % DEFAULT_START_DELAY_S)
    start.add_argument("--start-at", metavar="TIME",
                       help="start the video at this shared time, as main.py takes it")
    parser.add_argument("--gui", action="store_true", help="open gui.py")
    return parser


def parseArguments(argv, now):
    """!
    @brief Reads the command line and rejects wrong combinations before anything starts.

    @param argv Command-line arguments list, or None for sys.argv [none].
    @param now Function giving the current time as a datetime [none].
    @return [argparse.Namespace] The parsed options.
    @throws SystemExit With code 2 for a wrong option, and with code 0 for --help.
    """
    parser = buildParser()
    args = parser.parse_args(argv)
    hasStart = args.start_in is not None or args.start_at is not None
    if args.gui and (args.side or hasStart):
        parser.error("--gui cannot be combined with --left, --right, --start-in or --start-at")
    if args.image and hasStart:
        parser.error("a picture has no start time: leave out --start-in and --start-at")
    if hasStart and not args.gui and not args.side:
        parser.error("--start-in and --start-at need --left or --right")
    if args.start_at is not None:
        try:
            parseStartTime(args.start_at)
        except ValueError as e:
            parser.error(str(e))
    if args.start_in is not None:
        try:
            startTimeAfter(now(), args.start_in)
        except OverflowError:
            parser.error("--start-in is too large: %g" % args.start_in)
    return args


def settingsFor(args):
    """!
    @brief Chooses the settings file.

    @param args The parsed options.
    @return Settings file [string], relative to ROOT.
    """
    return IMAGE_SETTINGS if args.image else VIDEO_SETTINGS


def startTimeAfter(now, seconds):
    """!
    @brief Gives the time some seconds after now, rounded up to a whole second.

    @param now The current time as a datetime [none].
    @param seconds The delay [s].
    @return The time in START_TIME_FORMAT [string], which parseStartTime() accepts.
    @throws OverflowError If the time is too far ahead for a datetime.
    """
    target = now + datetime.timedelta(seconds=seconds)
    if target.microsecond:
        target = target.replace(microsecond=0) + datetime.timedelta(seconds=1)
    return target.strftime(START_TIME_FORMAT)


def resolveStartTime(args, now):
    """!
    @brief Gives the start time to pass to main.py.

    @param args The parsed options.
    @param now Function giving the current time as a datetime [none].
    @return The start time text [string], or None for a preview, a picture or the GUI.
    """
    if not args.side or args.image:
        return None
    if args.start_at is not None:
        return args.start_at.strip()
    delay = DEFAULT_START_DELAY_S if args.start_in is None else args.start_in
    return startTimeAfter(now(), delay)


def buildCommand(args, startTime=None):
    """!
    @brief Chooses the program and its arguments.

    @param args The parsed options.
    @param startTime The start time from resolveStartTime(), or None [none].
    @return The command [list], to run from ROOT.
    """
    settings = settingsFor(args)
    if args.gui:
        return [sys.executable, "gui.py", settings]
    if not args.side:
        return [sys.executable, os.path.join("tools", "preview_both.py"), settings,
                "--projector-gamma", PREVIEW_PROJECTOR_GAMMA]
    command = [sys.executable, "main.py", settings, "--side", args.side]
    if startTime is not None:
        command += ["--start-at", startTime]
    return command


def secondLaptopCommand(side, startTime, env=None):
    """!
    @brief Gives the command to type on the other laptop.

    @param side The side of this laptop, "LEFT" or "RIGHT" [none].
    @param startTime The shared start time [none].
    @param env Environment variables, only given by tests. uv run sets UV [none].
    @return The command [string], quoted for a shell.
    """
    env = os.environ if env is None else env
    python = ["uv", "run", "python"] if "UV" in env else ["python"]
    other = "--right" if side == "LEFT" else "--left"
    return shlex.join(python + ["instant_run.py", other, "--start-at", startTime])


def startMessage(side, startTime, env=None):
    """!
    @brief Gives the text about the start time and the second laptop.

    @param side The side of this laptop, "LEFT" or "RIGHT" [none].
    @param startTime The shared start time [none].
    @param env Environment variables, only given by tests [none].
    @return [string], The text to print.
    """
    return ("The video starts at %s.\n"
            "On the second laptop, in the repository folder, run:\n"
            "    %s\n"
            "Both laptops need the same clock and time zone, set to automatic time.\n"
            "A laptop that starts late joins at the right frame."
            % (startTime, secondLaptopCommand(side, startTime, env)))


def tkinterAvailable():
    """!
    @brief Tells whether this Python can import tkinter.

    The import can work although the window later fails, so this does not promise a window.

    @return [bool], True if the import works.
    """
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return False
    return True


def removeFile(path):
    """!
    @brief Removes a file if it is there.

    @param path Path of the file.
    @return None.
    """
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def ensureVideo(settingsFile, run):
    """!
    @brief Makes the test video if the settings file points at a video that is missing.

    A half-written video is removed, because the next run would otherwise try to play it.

    @param settingsFile Settings file, relative to ROOT.
    @param run Function that runs a command and gives its exit code [none].
    @return [bool] True if the video is there now. False after printing the reason.
    @throws KeyboardInterrupt If Ctrl-C is pressed while the video is made.
    """
    setup = SetupClass()
    try:
        setup.load(os.path.join(ROOT, settingsFile))
    except (OSError, ValueError) as e:
        print("Cannot read %s: %s" % (settingsFile, e), file=sys.stderr)
        return False
    path = setup.getSourcePath()
    if os.path.isfile(path):
        return True
    print("%s is missing, making it first." % path, flush=True)
    command = [sys.executable, os.path.join("tools", "make_test_video.py"), path]
    print("Running: %s" % shlex.join(command), flush=True)
    try:
        code = run(command)
    except KeyboardInterrupt:
        removeFile(path)
        raise
    if code == 0 and os.path.isfile(path):
        return True
    removeFile(path)
    print("Cannot make the test video %s (exit code %d)." % (path, code), file=sys.stderr)
    return False


def runCommand(command):
    """!
    @brief Runs a command from ROOT and waits for it.

    The command gets its own session, so Ctrl-C reaches only this launcher, which then
    stops the command. Otherwise main.py would print a traceback.

    @param command The command [none].
    @return Its exit code [int]. A program ended by a signal gives 128 + the signal number.
    @throws KeyboardInterrupt If Ctrl-C is pressed.
    """
    code = subprocess.run(command, cwd=ROOT, start_new_session=True).returncode
    return 128 - code if code < 0 else code


def launch(args, run, now, hasTkinter):
    """!
    @brief Prepares what the command needs, then runs it.

    The start time is taken after the test video is made, so making it does not use up the delay.

    @param args The parsed options.
    @param run Function that runs a command and gives its exit code [none].
    @param now Function giving the current time as a datetime [none].
    @param hasTkinter Function telling whether tkinter can be imported [none].
    @return [int] Exit code of the program, or EXIT_ERROR if it could not be started.
    @throws KeyboardInterrupt If Ctrl-C is pressed.
    """
    if args.gui and not hasTkinter():
        print(TKINTER_HELP, file=sys.stderr)
        return EXIT_ERROR
    if not args.image and not ensureVideo(settingsFor(args), run):
        return EXIT_ERROR
    startTime = resolveStartTime(args, now)
    command = buildCommand(args, startTime)
    if startTime is not None:
        print(startMessage(args.side, startTime))
    print("Running: %s" % shlex.join(command), flush=True)
    return run(command)


def main(argv=None, run=runCommand, now=datetime.datetime.now, hasTkinter=tkinterAvailable):
    """!
    @brief Reads the options and runs the chosen program.

    @param argv Command-line arguments list, or None for sys.argv [none].
    @param run Function that runs a command and gives its exit code. Tests give their own [none].
    @param now Function giving the current time as a datetime. Tests give their own [none].
    @param hasTkinter Function telling whether tkinter can be imported. Tests give their own [none].
    @return Exit code [int].
    @throws SystemExit With code 2 for a wrong option, and with code 0 for --help.
    """
    args = parseArguments(argv, now)
    try:
        return launch(args, run, now, hasTkinter)
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)
        return EXIT_INTERRUPTED


if __name__ == "__main__":
    sys.exit(main())
