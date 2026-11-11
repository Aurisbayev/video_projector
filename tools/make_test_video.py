#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""!
@brief Write a short test video: a grid with a bar that sweeps across the whole picture.

python tools/make_test_video.py [out.mp4] [--seconds 8] [--fps 30] [--size 3456x1080]

The bar crosses the overlap twice per loop, so a bad blend shows up as a flash or a dark band.
"""
import argparse
import sys

import cv2
import numpy as np


def drawFrame(width, height, progress):
    frame = np.full((height, width, 3), 40, np.uint8)
    step = max(width // 24, 20)
    for x in range(0, width, step):
        cv2.line(frame, (x, 0), (x, height), (90, 90, 90), 1)
    for y in range(0, height, step):
        cv2.line(frame, (0, y), (width, y), (90, 90, 90), 1)
    barWidth = max(width // 40, 8)
    x = int(progress * (width - barWidth))
    frame[:, x:x + barWidth] = (255, 255, 255)
    cv2.putText(frame, "%3d%%" % round(progress * 100), (width // 2 - 120, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 4.0, (0, 220, 255), 6, cv2.LINE_AA)
    return frame


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write a test video for the blend.")
    parser.add_argument("out", nargs="?", default="test_images/demo.mp4")
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--size", default="3456x1080", help="WIDTHxHEIGHT in pixels")
    args = parser.parse_args(argv)
    try:
        width, height = (int(v) for v in args.size.lower().split("x"))
    except ValueError:
        print("--size must look like 3456x1080", file=sys.stderr)
        return 1
    frames = max(2, int(args.seconds * args.fps))
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (width, height))
    if not writer.isOpened():
        print("Cannot write %s" % args.out, file=sys.stderr)
        return 1
    for i in range(frames):
        # Out and back, so the loop has no jump.
        t = i / (frames - 1)
        writer.write(drawFrame(width, height, 1 - abs(2 * t - 1)))
    writer.release()
    print("wrote %s (%d frames, %dx%d, %g fps)" % (args.out, frames, width, height, args.fps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
