#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import os

import cv2
import numpy as np
# ˄


class Image(object):
    """!
    @brief Provides a wrapper around a NumPy array represnting an image or video frame Holds one image in memory.

    @details Image is the Python object that stores and manages the frame. numpy.ndarray is the actual pixel data. This class wraps the OpenCV image (Numpy array, BGR, 8 bits).
    """

    # ˅
    
    # ˄

    def load(self, path):
        """!
        @brief Reads the file at path as a color image and stores it inside the object.

        @param path A string containing the image-file path.
        @returns frame A NumPy array, stored inside the Image object.
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
        @brief Retrieves the stored pixel array.
        @returns frame if load() is successful, None if not.
        """

        # ˅
        
        return self.__frame
        # ˄

    def getShape(self):
        """!
        @brief Retrieves the array's dimensions.
        @returns tuple (height, width, channels)
        @throws ValueError if nothing is loaded
        """

        # ˅
        
        if self.__frame is None:
            raise ValueError("No frame is loaded: call load() first")
        return self.__frame.shape
        # ˄

    def __init__(self):
        """!
        @brief Initializes the object but contains no image initially.
        """

        self.__frame = None

        # ˅
        pass
        # ˄

    # ˅
    ## @fn __init__(self)
    #  @brief Creates an Image that holds no picture until load() or setFrame() is called.

    def setFrame(self, frame):
        """!
        @brief Stores a NumPy Array in the Image object without reading a file.
        @details Used for the results of scaling, cropping and masking.
        @param frame A NumPy array.
        @throws ValueError if frame is not a NumPy array.
        """
        
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy.ndarray, got {type(frame).__name__}")
        self.__frame = frame
    # ˄


# ˅

# ˄
