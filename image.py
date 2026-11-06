#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import os

import cv2
import numpy as np
# ˄


class Image(object):
    # ˅
    """!
    @brief A picture held in memory, also used for one frame of a video.

    It wraps the NumPy array that OpenCV uses for a picture.
    """
    # ˄

    def load(self, path):
        # ˅
        """!
        @brief Reads the file at path as a colour picture and keeps it inside the object.

        The picture is loaded in BGR (cv2.IMREAD_COLOR). It can be read later via getFrame()
        and getShape().

        @param path Location of the picture (string).
        @return The frame (NumPy array).
        @rtype numpy.ndarray
        @throws FileNotFoundError If there is no such file.
        @throws ValueError If the path is empty or not text, or the file cannot be read as a
                picture.
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
        @brief Gives the picture data.

        @return The frame, or None if nothing is loaded or set yet.
        @rtype numpy.ndarray or None
        """
        return self.__frame
        # ˄

    def getShape(self):
        # ˅
        """!
        @brief Gives the picture size.

        @return (height, width, channels). A frame from setFrame() without colour channels
                gives (height, width).
        @rtype tuple
        @throws ValueError If nothing is loaded.
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
    ## @fn __init__(self)
    #  @brief Creates an Image that holds no picture until load() or setFrame() is called.

    def setFrame(self, frame):
        """!
        @brief Puts new picture data into the object, instead of loading it from a file.

        Used for video frames and for the results of scaling, cropping and masking.

        @param frame The new picture data (NumPy array).
        @return None
        @throws ValueError If frame is not a NumPy array.
        """
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy.ndarray, got {type(frame).__name__}")
        self.__frame = frame
    # ˄


# ˅

# ˄
