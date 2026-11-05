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
        """!
        @brief Load the image at path in BGR (cv2.IMREAD_COLOR) and return it as a numpy.ndarray.
        
        The loaded frame is also kept internally and can be read via getFrame() / getShape().
        
        @param path path to the image file [none].
        @return The loaded image as a numpy array [none].
        @rtype numpy.ndarray
        @throws FileNotFoundError If the file does not exist or is not a file.
        @throws ValueError If it cannot be read as an image, if path is not a non-empty string, if cv2 returns None, or if the result is not a numpy array.
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
        """!
        @brief Return the loaded frame, or None if load() has not been called yet.
        @return The loaded frame [none].
        @rtype numpy.ndarray
        """
        return self.__frame
        # ˄

    def getShape(self):
        # ˅
        """!
        @brief Return (height, width, channels) of the loaded frame.
        @return A tuple of (height, width, channels) [none].
        @rtype tuple
        @throws ValueError If load() has not been called yet (self.__frame is None).
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
        """!
        @brief Hold an already-built frame (numpy.ndarray) instead of loading one from a file.
        @param frame The already-built frame to hold [none].
        @return None
        @rtype None
        @throws ValueError If frame is not a numpy.ndarray.
        """
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy.ndarray, got {type(frame).__name__}")
        self.__frame = frame
    # ˄


# ˅

# ˄
