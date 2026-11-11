#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import os

import cv2
import numpy as np
# ˄


class Image(object):
    """!
    @brief Stores and manages one image or video frame. 

    @details The pixel data is held in a numpy.ndarray using OpenCV's colour-image
    representation (BGR, 8 bits per channel). The Image object is a wrapper; the array is the actual pixel data.

    \par Class Attributes:
    frame [ndarray], Stored image pixel data as a numpy.ndarray, or None before an image is set.
    """
    # ˅
    
    # ˄

    def load(self, path):
        """!
        @brief Reads a color image from a file and stores it pixel array.

        @param path [string] Path to the image file.
        @returns numpy.ndarray The loaded image frame, stored inside the Image object.

        @throws FileNotFoundError if there is no such file. 
        @throws ValueError if the path is empty or the file cannot be read as a picture.
        """

        # ˅
        
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
        """!
        @brief Returns the pixel array currently stored in this object.
        @returns numpy.ndarray The stored frame, or None if no frame has been loaded or set.
        """

        # ˅
        
        return self.__frame
        # ˄

    def getShape(self):
        """!
        @brief Returns the dimensions of the stored pixel array.
        @returns tuple Array's shape in the form (height, width, channels).
        @throws ValueError if no frame is stored.
        """

        # ˅
        
        if self.__frame is None:
            raise ValueError("No frame is loaded: call load() first")
        return self.__frame.shape
        # ˄

    def __init__(self):
        """!
        @brief Initializes the Image object with no frame stored.
        """

        self.__frame = None

        # ˅
        pass
        # ˄

    # ˅

    def setFrame(self, frame):
        """!
        @brief Stores an existing NumPy array as this object's image frame.

        @details Used for the results of scaling, cropping and masking.

        @param frame [ndarray] Image pixel data.
        @throws ValueError if frame is not a NumPy array.
        """
        
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy.ndarray, got {type(frame).__name__}")
        self.__frame = frame
    # ˄


# ˅

# ˄
