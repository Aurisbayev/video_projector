"""!
@brief Main execution script for the projector application.

Command-line options:
python main.py settings.json [--side LEFT|RIGHT] [--scale-mode crop|fit] [--start-at TIME]

Options:
- settings: Path of the settings file.
- --side: Overrides projectorSide. Not case sensitive.
- --scale-mode: Overrides scaleMode. Not case sensitive.
- --start-at TIME: Shared start time for a video, as HH:MM, HH:MM:SS, YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS, local time. Same time on both computers. Both computers must have the right clock and the same time zone. For a picture the option is ignored and a warning is logged: "--start-at is ignored: the source is a picture, not a video". A time in the wrong form is a usage error.

Exit codes:
- 0: Normal end (the window was closed with q or Esc, or the picture window was closed with a key)
- 1: The settings file, the picture or the video could not be read or opened (message names the problem)
- 2: validate() returned False; or a wrong command-line option, including a wrong --start-at or --scale-mode
"""


import argparse
import logging
import sys

from pipeline_class import PipelineClass
from setup_class import SetupClass
from side import Side
from video_source import parseStartTime

_log = logging.getLogger(__name__)

## Exit code 0: normal end.
EXIT_OK = 0
## Exit code 1: the settings file, the picture or the video could not be read or opened.
EXIT_ERROR = 1
## Exit code 2: validate() returned False. A wrong command-line option gives the same code through argparse.
EXIT_INVALID = 2


def main(argv=None):
    """!
    @brief Executes the main program flow including parsing options, loading settings, and running the pipeline.

    Order inside main(): read the options (a wrong --start-at stops here), load the settings, apply --side and --scale-mode, validate(), create the pipeline, set the start time (video only), run().

    @param argv Command-line arguments list [none].
    @return Exit code indicating success (0), read/open error (1), or validation/option error (2) [none].
    @rtype int
    @throws SystemExit argparse raises this with code 2 for invalid command-line arguments,
            also for a bad --start-at time, and with code 0 for --help.

    Only OSError and ValueError are turned into exit code 1. Any other error, such as
    cv2.error from the window, ends the program with a traceback. If the source file does
    not exist, validate() fails, so the exit code is 2. If argv is None, argparse reads
    sys.argv.
    """
    parser = argparse.ArgumentParser(
        description="Show this computer's half of the dual-projector picture.")
    parser.add_argument("settings", help="path to the settings JSON file")
    parser.add_argument("--side", choices=["LEFT", "RIGHT"], type=str.upper,
                        help="which projector this computer drives (overrides projectorSide "
                             "in the settings file)")
    parser.add_argument("--scale-mode", choices=["crop", "fit"], type=str.lower,
                        help="crop fills the picture and cuts the edges, fit shows the whole "
                             "picture with black bars (overrides scaleMode in the settings file)")
    parser.add_argument("--start-at", metavar="TIME",
                        help="start a video at this shared time, for example 14:30:05 "
                             "(local time). Give the same time on both computers; their "
                             "clocks must be set right. Without it a key press starts the video")
    args = parser.parse_args(argv)

    startAt = None
    if args.start_at is not None:
        try:
            startAt = parseStartTime(args.start_at)
        except ValueError as e:
            parser.error(str(e))

    logging.basicConfig(level=logging.INFO)

    setup = SetupClass()
    try:
        setup.load(args.settings)
    except (OSError, ValueError) as e:
        _log.error("Cannot load settings: %s", e)
        return EXIT_ERROR

    if args.side:
        setup.setProjectorSide(Side[args.side])
    if args.scale_mode:
        setup.setScaleMode(args.scale_mode)

    if not setup.validate():
        return EXIT_INVALID

    try:
        pipeline = PipelineClass(setup)
        if startAt is not None:
            if pipeline.isVideo():
                pipeline.setStartAt(startAt)
            else:
                _log.warning("--start-at is ignored: the source is a picture, not a video")
        pipeline.run()
    except (OSError, ValueError) as e:
        _log.error("Cannot run: %s", e)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
