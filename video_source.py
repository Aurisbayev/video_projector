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
    """!
    @brief Reads a video file one frame at a time.

    PipelineClass uses this class to play a video. It is a helper class: it does no
    projection calculations.
    """
    ## File extensions treated as video, compared in lower case.
    VIDEO_EXTENSIONS = (".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm")
    ## Frame rate used if the file reports no frame rate, or an unusable one [frames per second].
    DEFAULT_FPS = 30.0
    # ˄

    @staticmethod
    def isVideoPath(path):
        # ˅
        """!
        @brief Tells whether a path has a video file extension.

        Only the extension is checked (in VIDEO_EXTENSIONS). The file is not opened.

        @param path Path of a picture or video file.
        @return True if the extension is a video extension. False otherwise, also for
                anything that is not text.
        @rtype bool
        """
        if not isinstance(path, str):
            return False
        return os.path.splitext(path)[1].lower() in VideoSource.VIDEO_EXTENSIONS
        # ˄

    def getFps(self):
        # ˅
        """!
        @brief Gives the frame rate of the video.

        @return Number of frames per second [frames per second].
        @rtype float
        """
        return self.__fps
        # ˄

    def getFrameCount(self):
        # ˅
        """!
        @brief Gives the number of frames in the video.

        @return Number of frames.
        @rtype int
        """
        return self.__frameCount
        # ˄

    def getShape(self):
        # ˅
        """!
        @brief Gives the size of one frame of the video.

        @return (height, width, 3): height [px], width [px] and the 3 colour channels.
        @rtype tuple
        """
        return (self.__height, self.__width, 3)
        # ˄

    def frameAt(self, index):
        # ˅
        """!
        @brief Gives one frame of the video.

        The next frame is read on. A later frame is reached by skipping the frames in
        between, and an earlier one (when the video loops) by seeking back. Asking for the
        same frame twice in a row gives the stored picture without reading again.

        @param index Frame number, counted from 0.
        @return The frame as a NumPy array (BGR colours, 8 bits per colour).
        @rtype numpy.ndarray
        @throws ValueError If the video is closed, the index is out of range or not an
                integer, or the frame cannot be skipped to or read.
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
        """!
        @brief Releases the video file.

        A second call does nothing.

        @return None
        """
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
    ## @fn __init__(self, path)
    #  @brief Opens a video file and reads its frame rate, frame count and frame size.
    #
    #  If the file reports no usable frame rate, DEFAULT_FPS is used.
    #
    #  @param path Path of the video file.
    #  @throws ValueError If path is empty or not text.
    #  @throws FileNotFoundError If the file does not exist.
    #  @throws ValueError If the file is corrupt or OpenCV does not support its codec.
    #  @throws ValueError If the number of frames cannot be found.

    # ˄


# ˅
START_TIME_FORMATS = ("%H:%M", "%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def parseStartTime(text, now=None):
    """!
    @brief Turns a start time typed by a person into seconds since 1970, the same kind of number time.time() gives.

    Accepted forms are HH:MM, HH:MM:SS (today, local time) and YYYY-MM-DD HH:MM, YYYY-MM-DD HH:MM:SS (that day, local time). Spaces around the text are ignored, and a time that has already passed is accepted.

    @param text The start time string to parse [none].
    @param now The current time as a datetime, only given by tests [none].
    @return The parsed time in seconds since 1970 [s].
    @rtype float
    @throws ValueError If the input is not text, or if the text does not match the accepted forms (including impossible times like 25:00).
    """
    # Turn a start time typed by a person into seconds since 1970 (like time.time()).
    #
    # text: "HH:MM", "HH:MM:SS" (today, local time) or "YYYY-MM-DD HH:MM[:SS]"
    # now: the current time as a datetime, only given by tests
    # A time that has already passed is fine: the video then joins at the frame that belongs
    # to that moment. Raises ValueError if the text is not one of these forms.
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
