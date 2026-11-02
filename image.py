#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import os

import cv2
import numpy as np
# ˄


class Image(object):
    # ˅
    
    # ˄

    def load(self, path):
        # ˅
        """Load the image at path in BGR (cv2.IMREAD_COLOR) and return it as a numpy.ndarray.

        path: path to the image file
        The loaded frame is also kept internally and can be read via getFrame() / getShape().
        Raises FileNotFoundError if the file does not exist or is not a file, and
        ValueError if it cannot be read as an image.
        """
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"path must be a non-empty string, got {path!r}")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image file not found: '{path}'")
        frame = cv2.imread(path, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(
                f"Failed to read image '{path}': the file is corrupt "
                "or its format is not supported by OpenCV"
            )
        if not isinstance(frame, np.ndarray):
            raise ValueError(
                f"cv2.imread returned {type(frame).__name__} instead of "
                f"numpy.ndarray for '{path}'"
            )
        self.__frame = frame
        return frame
        # ˄

    def getFrame(self):
        # ˅
        """Return the loaded frame, or None if load() has not been called yet."""
        return self.__frame
        # ˄

    def getShape(self):
        # ˅
        """Return (height, width, channels) of the loaded frame.

        Raises ValueError if load() has not been called yet.
        """
        if self.__frame is None:
            raise ValueError("No frame is loaded: call load() first")
        return self.__frame.shape
        # ˄

    def __init__(self):

        self.__frame = None

        # ˅
        pass
        # ˄

    # ˅
    def setFrame(self, frame):
        """Hold an already-built frame (numpy.ndarray) instead of loading one from a file.

        Raises ValueError if frame is not a numpy.ndarray.
        """
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy.ndarray, got {type(frame).__name__}")
        self.__frame = frame
    # ˄


# ˅

# ˄
