import argparse
import logging
import sys

from pipeline_class import PipelineClass
from setup_class import SetupClass
from side import Side
from video_source import parseStartTime

_log = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INVALID = 2


def main(argv=None):
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
