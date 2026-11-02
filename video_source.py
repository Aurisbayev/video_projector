#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import datetime
import math
import os

import cv2
import numpy as np
# ˄


class VideoSource(object):
    # ˅
    VIDEO_EXTENSIONS = (".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm")
    DEFAULT_FPS = 30.0
    # ˄

    @staticmethod
    def isVideoPath(path):
        # ˅
        """Return True if the file extension of path is a supported video type.

        path: path to a picture or video file (string)
        Only the extension is checked, the file is not opened.
        """
        if not isinstance(path, str):
            return False
        return os.path.splitext(path)[1].lower() in VideoSource.VIDEO_EXTENSIONS
        # ˄

    def getFps(self):
        # ˅
        """Return the frame rate of the video [frames per second]."""
        return self.__fps
        # ˄

    def getFrameCount(self):
        # ˅
        """Return the number of frames in the video."""
        return self.__frameCount
        # ˄

    def getShape(self):
        # ˅
        """Return (height, width, channels) of one video frame."""
        return (self.__height, self.__width, 3)
        # ˄

    def frameAt(self, index):
        # ˅
        """Return frame number index (counted from 0) as a BGR numpy.ndarray.

        index: frame number, 0 <= index < getFrameCount()
        Asking for the next frame reads on, asking for a later one skips the frames in
        between, and asking for an earlier one (for example when the video loops) seeks back.
        The same frame is returned again if it is asked for twice in a row.
        Raises ValueError if the index is out of range or the frame cannot be read.
        """
        if self.__capture is None:
            raise ValueError("The video is closed")
        if not isinstance(index, (int, np.integer)) or not 0 <= index < self.__frameCount:
            raise ValueError("Frame index %r is outside 0..%d" % (index, self.__frameCount - 1))
        index = int(index)
        if index == self.__lastIndex:
            return self.__lastFrame
        if index < self.__next:
            self.__capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            self.__next = index
        while self.__next < index:
            if not self.__capture.grab():
                raise ValueError("Failed to skip to frame %d of '%s'" % (index, self.__path))
            self.__next += 1
        ok, frame = self.__capture.read()
        if not ok or frame is None:
            raise ValueError("Failed to read frame %d of '%s'" % (index, self.__path))
        self.__next = index + 1
        self.__lastIndex = index
        self.__lastFrame = frame
        return frame
        # ˄

    def close(self):
        # ˅
        """Release the video file. Does nothing on calls after the first."""
        if self.__capture is not None:
            self.__capture.release()
            self.__capture = None
        # ˄

    def __init__(self, path):

        self.__path = None

        self.__capture = None

        self.__fps = None

        self.__frameCount = None

        self.__width = None

        self.__height = None

        self.__next = 0

        self.__lastIndex = None

        self.__lastFrame = None

        # ˅
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string, got %r" % (path,))
        if not os.path.isfile(path):
            raise FileNotFoundError("Video file not found: '%s'" % path)
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            capture.release()
            raise ValueError("Failed to open video '%s': the file is corrupt "
                             "or its codec is not supported by OpenCV" % path)
        frameCount = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frameCount <= 0:
            capture.release()
            raise ValueError("Cannot tell how many frames video '%s' has" % path)
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not fps or not math.isfinite(fps) or fps <= 0:
            fps = VideoSource.DEFAULT_FPS
        self.__path = path
        self.__capture = capture
        self.__fps = float(fps)
        self.__frameCount = frameCount
        self.__width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.__height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # ˄

    # ˅

    # ˄


# ˅
START_TIME_FORMATS = ("%H:%M", "%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def parseStartTime(text, now=None):
    """Turn a start time typed by a person into seconds since 1970 (like time.time()).

    text: "HH:MM", "HH:MM:SS" (today, local time) or "YYYY-MM-DD HH:MM[:SS]"
    now: the current time as a datetime, only given by tests
    A time that has already passed is fine: the video then joins at the frame that belongs
    to that moment. Raises ValueError if the text is not one of these forms.
    """
    if not isinstance(text, str):
        raise ValueError("Start time must be text like 14:30:05, got %r" % (text,))
    text = text.strip()
    now = datetime.datetime.now() if now is None else now
    for form in START_TIME_FORMATS:
        try:
            parsed = datetime.datetime.strptime(text, form)
        except ValueError:
            continue
        if "%Y" not in form:
            parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
        return parsed.timestamp()
    raise ValueError("Start time must look like 14:30:05 or 2026-11-05 14:30:05, got %r" % text)
# ˄
