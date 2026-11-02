#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show the full-screen test pattern on the chosen screen (D-44)."""
import argparse
import os
import sys

# Scripts in tools/ import modules from the repository root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from display import Display


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Show the PBL4 test pattern full-screen."
    )
    parser.add_argument(
        "--screen",
        type=int,
        default=0,
        help="screen index to display on (default: 0)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="test pattern width in pixels (default: 1280)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="test pattern height in pixels (default: 720)",
    )
    args = parser.parse_args(argv)

    frame = Display.buildTestImage(args.width, args.height)
    display = Display(screen=args.screen)

    try:
        display.show(frame)
        display.setFullscreen(True)
        while display.waitKey(0) == -1:
            pass
    finally:
        display.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
