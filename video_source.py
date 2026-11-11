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
    """!
    @brief Opens a video file and provides access to its frames by index.
    @details 

    \par Class Attributes:
    path [string] Path to the video file.
    fps [double] Video frame rate in frames per second.
    frameCount [int] Total number of frames in the video.
    width [int] Frame width in pixels.
    height [int] Frame height in pixels.
    next [int] Index of the next frame position to read.
    lastIndex [int] Index of the cached frame.
    lastFrame [ndarray] Cached video frame.
    """

    # ˅
    
    ## File extensions treated as video, compared in lower case.
    VIDEO_EXTENSIONS = (".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm")
    ## Frame rate used if the file reports no frame rate, or an unusable one [frames per second].
    DEFAULT_FPS = 30.0
    # ˄

    @staticmethod
    def isVideoPath(path):
        """!
    @brief Determines whether a path is a recognized video file extension.
    @details The comparison is case-insensitive.
    @param [path] a string file path.
    @return [bool] True if the extension is in VIDEO_EXTENSIONS; otherwise False.
    """

        # ˅
        
        if not isinstance(path, str):
            return False
        return os.path.splitext(path)[1].lower() in VideoSource.VIDEO_EXTENSIONS
        # ˄

    def getFps(self):
        """!
        @brief Returns the video's frame rate.
        @return [double] Frames per second. DEFAULT_FPS is used if OpenCV reports an 
        unusable frame rate. 
        """

        # ˅
        
        return self.__fps
        # ˄

    def getFrameCount(self):
        """!
        @brief Returns the total number of frames reported for the video.
        @return [int] Number of frames.
        """

        # ˅
        
        return self.__frameCount
        # ˄

    def getShape(self):
        """!
        @brief Returns the dimensions of a video frame.
        @return [tuple] Frame shape as (height, width, 3), where 3 is the BGR channel count.
        """

        # ˅
        
        return (self.__height, self.__width, 3)
        # ˄

    def frameAt(self, index):
        """!
        @brief Retrieves the video frame at the requested index (zero-based).

        @details Returns the cached frame when the requested index is the cached index.
        For later frames, it reads and skips the frames in between. 
        For earlier frames, it moves the video back to the requested position before reading
        
        @param index [int], Zero-based frame index.
        @return [ndarray], Requested video frame.
        @throws ValueError If the video is closed, index is outside the value range,
        or the frame cannot be skipped to or read.
        """

        # ˅
        
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
        """!
        @brief Releases the video file and frees the resources used to read it.
        @return None.
        """

        # ˅
        
        if self.__capture is not None:
            self.__capture.release()
            self.__capture = None
        # ˄

    def __init__(self, path):
        """!
        @brief Opens a video and reads its basic properties

        @param [path] a string file path.

        @throws ValueError if path is empty, the video cannot be opened/decoded, 
        or its frame count is not positive
        @throws FileNotFoundError if the video file could not be found.
        """


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
    """!
    @brief Converts a human-readable start time into a Unix timestamp.

    @details Accepted formats are HH:MM, HH:MM:SS, YYYY-MM-DD HH:MM, 
    and YYYY-MM-DD HH:MM:SS. 
    
    @param text [string], String containing the time to start.
    @param now Optional datetime.datetime used as the reference date; defaults to 
    the current local date and time; mainly for testing purposes.

    @return [float] Unix timestamp in seconds.
    
    @throws ValueError If text is not a string or does not match a supported format.
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
