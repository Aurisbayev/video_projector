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
        
        return self.__frame
        # ˄

    def getShape(self):
        # ˅
        
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
        
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy.ndarray, got {type(frame).__name__}")
        self.__frame = frame
    # ˄


# ˅

# ˄
