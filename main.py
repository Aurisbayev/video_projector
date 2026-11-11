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
    @brief Runs the dual-projector program from command-line arguments.

    @param argy Command-line arguments. If None, argparse reads sys.argy.

    @return Exit code 0 for normal completion.
    @return Exit Code 1 if the settings or source picture cannot be read or the pipeline fail.
    @return Exit code 2 if settings are unusabel or the command-line arguments are invalid.

    @throws SystemExit argparse raises this for invalid command-line arguments.
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
