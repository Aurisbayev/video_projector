#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""!
@brief Preview both projectors on one computer: run LEFT and RIGHT, join them, show the result.

python tools/preview_both.py settings.json [--save out.png] [--no-window] [--projector-gamma 2.2]

If sourcePath is a video, it plays with both sides joined (q or Esc quits, space pauses).
With --save the first frame is written. Use --no-window to only save.
"""
import argparse
import os
import sys
import time

import cv2
import numpy as np

# Scripts in tools/ import modules from the repository root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from display import Display
from math_class import MathClass
from pipeline_class import PipelineClass
from setup_class import SetupClass
from side import Side
from video_source import VideoSource

MAX_WINDOW_WIDTH = 1600


def renderSide(settingsPath, side=None):
    """Run the pipeline steps for one settings file, without opening a projector window.

    side: Side to use instead of the projectorSide in the file (None keeps the file's).
    """
    setup = SetupClass()
    setup.load(settingsPath)
    if side is not None:
        setup.setProjectorSide(side)
    if not setup.validate():
        raise ValueError("Invalid settings: %s" % settingsPath)
    pipeline = PipelineClass(setup)
    pipeline.load()
    pipeline.scaleSource()
    return setup, pipeline.applyMask(pipeline.crop()).getFrame()


def buildPipeline(settingsPath, side):
    """Return (setup, PipelineClass) for one side, without opening a projector window."""
    setup = SetupClass()
    setup.load(settingsPath)
    setup.setProjectorSide(side)
    if not setup.validate():
        raise ValueError("Invalid settings: %s" % settingsPath)
    return setup, PipelineClass(setup)


def fitToWindow(frame):
    """Shrink a wide picture so it fits the preview window."""
    if frame.shape[1] <= MAX_WINDOW_WIDTH:
        return frame
    scale = MAX_WINDOW_WIDTH / frame.shape[1]
    return cv2.resize(frame, (MAX_WINDOW_WIDTH, round(frame.shape[0] * scale)),
                      interpolation=cv2.INTER_AREA)


def playVideoPreview(settingsPath, save=None, window=True, clock=time.monotonic, projectorGamma=None):
    """Play the video with LEFT and RIGHT joined, the way the screen would look.

    save: path to write the first joined frame to (None writes nothing)
    window: False shows nothing and stops after the first frame
    projectorGamma: see join()
    Keys: q or Esc quits, space pauses. Returns the overlap in pixels.
    """
    leftSetup, left = buildPipeline(settingsPath, Side.LEFT)
    _, right = buildPipeline(settingsPath, Side.RIGHT)
    overlapPx = MathClass.overlapPx(
        leftSetup.getProjectorResXY()[0],
        leftSetup.getImageWidthCm(),
        leftSetup.getProjectorSpacingCm())
    source = VideoSource(leftSetup.getSourcePath())

    def joinedAt(index):
        raw = source.frameAt(index)
        return join(left.processFrame(raw).getFrame(), right.processFrame(raw).getFrame(), overlapPx, projectorGamma)

    try:
        first = joinedAt(0)
        if save and not cv2.imwrite(save, first):
            raise OSError("Cannot write %s" % save)
        if not window:
            return overlapPx
        display = Display(windowName="preview")
        try:
            display.show(fitToWindow(first))
            start, paused, pausedAt = clock(), False, 0.0
            while True:
                now = pausedAt if paused else clock() - start
                index = int(now * source.getFps()) % source.getFrameCount()
                display.show(fitToWindow(joinedAt(index)))
                key = display.waitKey(1)
                if key != -1 and (key & 0xFF) in PipelineClass.QUIT_KEYS:
                    break
                if key != -1 and (key & 0xFF) == ord(" "):
                    if paused:
                        start = clock() - pausedAt
                    else:
                        pausedAt = clock() - start
                    paused = not paused
        finally:
            display.close()
    finally:
        source.close()
    return overlapPx


def join(leftFrame, rightFrame, overlapPx, projectorGamma=None):
    """Put the two pictures together where they overlap, as the light of the two projectors does.

    projectorGamma: None adds the pixel values. A number (about 2.2 for a real projector)
    adds the light instead: pixel values are turned into light with value ** projectorGamma,
    added, and turned back. This is what the wall shows, so it can be compared with a photo.
    """
    resY, resX = leftFrame.shape[:2]
    width = 2 * resX - overlapPx
    if projectorGamma is None:
        canvas = np.zeros((resY, width, 3), np.int32)
        canvas[:, :resX] += leftFrame
        canvas[:, resX - overlapPx:] += rightFrame
        return np.clip(canvas, 0, 255).astype(np.uint8)
    if not projectorGamma > 0:
        raise ValueError("projectorGamma must be positive, got %r" % (projectorGamma,))
    out = np.zeros((resY, width, 3), np.uint8)
    out[:, :resX - overlapPx] = leftFrame[:, :resX - overlapPx]
    out[:, resX:] = rightFrame[:, overlapPx:]
    if overlapPx > 0:
        light = ((leftFrame[:, resX - overlapPx:].astype(np.float64) / 255.0) ** projectorGamma
                 + (rightFrame[:, :overlapPx].astype(np.float64) / 255.0) ** projectorGamma)
        out[:, resX - overlapPx:resX] = np.rint(np.clip(light, 0.0, 1.0) ** (1.0 / projectorGamma) * 255.0).astype(np.uint8)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preview the LEFT and RIGHT pictures joined together.")
    parser.add_argument("left_file", help="settings file (LEFT if a second file is given)")
    parser.add_argument("right_file", nargs="?",
                        help="optional second settings file for RIGHT; without it the first "
                             "file is used for both sides")
    parser.add_argument("--save", metavar="PATH", help="also write the joined picture to this file")
    parser.add_argument("--no-window", action="store_true", help="do not open a window")
    parser.add_argument("--projector-gamma", type=float, metavar="G",
                        help="show what the wall looks like by adding the light of the two "
                             "projectors (G about 2.2); without it the pixel values are added")
    args = parser.parse_args(argv)

    try:
        probe = SetupClass()
        probe.load(args.left_file)
        if VideoSource.isVideoPath(probe.getSourcePath()):
            if args.right_file:
                raise ValueError("A video preview takes one settings file, not two")
            overlapPx = playVideoPreview(args.left_file, save=args.save,
                                         window=not args.no_window,
                                         projectorGamma=args.projector_gamma)
            if args.save:
                print("saved first frame %s (overlap %d px)" % (args.save, overlapPx))
            return 0
        if args.right_file:
            leftSetup, leftFrame = renderSide(args.left_file)
            _, rightFrame = renderSide(args.right_file)
        else:
            leftSetup, leftFrame = renderSide(args.left_file, Side.LEFT)
            _, rightFrame = renderSide(args.left_file, Side.RIGHT)
        overlapPx = MathClass.overlapPx(
            leftSetup.getProjectorResXY()[0],
            leftSetup.getImageWidthCm(),
            leftSetup.getProjectorSpacingCm())
        joined = join(leftFrame, rightFrame, overlapPx, args.projector_gamma)
    except (OSError, ValueError) as e:
        print("Cannot preview: %s" % e, file=sys.stderr)
        return 1

    if args.save:
        if not cv2.imwrite(args.save, joined):
            print("Cannot write %s" % args.save, file=sys.stderr)
            return 1
        print("saved %s (%dx%d, overlap %d px)" % (args.save, joined.shape[1], joined.shape[0], overlapPx))

    if not args.no_window:
        shown = fitToWindow(joined)
        display = Display(windowName="preview")
        try:
            display.show(shown)
            while display.waitKey(0) == -1:
                pass
        finally:
            display.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
