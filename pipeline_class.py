#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import logging
import math
import time

import cv2
import numpy as np

from display import Display, findProjectorScreens
from image import Image
from math_class import MathClass
from setup_class import SetupClass
from video_source import VideoSource

_log = logging.getLogger(__name__)

# ˄


class PipelineClass(object):
    # ˅
    # Keys that stop a video: Esc and q.
    QUIT_KEYS = (27, ord("q"))
    """!
    @var QUIT_KEYS
    @brief (27, ord("q")): Esc and q. Public and static
    """
    
    # ˄

    def load(self):
        # ˅
        # Image.load() raises FileNotFoundError / ValueError naming the path.
        path = self.__setup.getSourcePath()
        image = Image()
        image.load(path)
        self.__sourceFrame = image
        return image
        # ˄

    def crop(self):
        # ˅
        if self.__sourceFrame is None:
            raise ValueError("No source frame: call load() and scaleSource() first")

        frame = self.__sourceFrame.getFrame()
        if frame is None:
            raise ValueError("No source frame: call load() and scaleSource() first")

        resX, _resY = self.__setup.getProjectorResXY()
        region = self.__math.cropRegion(
            self.__setup.getProjectorSide(),
            resX,
            self.__setup.getImageWidthCm(),
            self.__setup.getProjectorSpacingCm(),
        )
        xStart = region.getXStartPx()
        width = region.getWidthPx()
        frameWidth = frame.shape[1]

        if xStart < 0 or width <= 0 or xStart + width > frameWidth:
            raise ValueError(
                "Region (%d, %d) does not fit inside scaled source frame width %d"
                % (xStart, width, frameWidth)
            )

        # Return a copy wrapped in Image so applyMask() cannot modify sourceFrame.
        result = Image()
        result.setFrame(frame[:, xStart:xStart + width].copy())
        return result
        # ˄

    def applyMask(self, sliceFrame):
        # ˅
        """!
        @brief Applies the blend mask to the cropped frame.
        
        Only columns that the mask fades are calculated now (columns with alpha 1 are coppied).
        
        @param sliceFrame The cropped portion of the frame to be masked [none]
        @return The masked frame [none]
        @rtype Image
        """
        if self.__mask is None:
            raise ValueError("No mask: the mask must be built before applyMask()")
        # The mask is built once elsewhere and only read here.
        alpha = np.asarray(self.__mask.getAlpha(), dtype=np.float64)
        frame = sliceFrame.getFrame()
        if frame.shape[1] != alpha.shape[0]:
            raise ValueError(
                f"Slice width {frame.shape[1]} does not match mask length {alpha.shape[0]}")
        # One multiplier per column, broadcast over rows and colour channels.
        # Columns with alpha 1 stay as they are, so only the faded columns are calculated.
        out = frame.astype(np.uint8, copy=True)
        faded = np.flatnonzero(alpha != 1.0)
        if faded.size:
            scale = alpha[faded].reshape((1, -1) + (1,) * (frame.ndim - 2))
            product = np.rint(frame[:, faded].astype(np.float64) * scale)
            out[:, faded] = np.clip(product, 0, 255).astype(np.uint8)
        result = Image()
        result.setFrame(out)
        return result
        # ˄

    def display(self, frame):
        # ˅
        if not isinstance(frame, Image):
            raise ValueError(
                "frame must be an Image, got %s" % type(frame).__name__
            )

        array = frame.getFrame()
        if array is None:
            raise ValueError("frame is empty: call load() and scaleSource() first")

        screens, screenIndex = findProjectorScreens()
        display = Display(screens=screens, screen=screenIndex)
        try:
            display.show(array)
            display.setFullscreen(True)
            while display.waitKey(0) == -1:
                pass
        finally:
            display.close()

        self.__output = frame
        # ˄

    def run(self):
        # ˅
        """!
        @brief Executes the pipeline processing.
        
        If isVideo() is true, it calls playVideo() and ends; otehrwise, the picture steps as before.
        
        @return None
        @rtype None
        """
        # The region and mask were built once in the constructor.
        if self.isVideo():
            self.playVideo()
            return
        self.load()
        self.scaleSource()
        sliceFrame = self.crop()
        self.display(self.applyMask(sliceFrame))
        # ˄

    def isVideo(self):
        # ˅
        """!
        @brief Checks if the source path has a video extension.
        
        @return True if sourcePath has a video extension, False otherwise [none].
        @rtype bool
        """
        return VideoSource.isVideoPath(self.__setup.getSourcePath())
        # ˄

    def setStartAt(self, startAt):
        # ˅
        """!
        @brief Sets the shared start time or clears it with None.
        
        @param startAt shared start time as seconds since 1970 [s], or None to start with a key press.
        @return None
        @rtype None
        @throws ValueError if the value is not a finite number or None
        """
        # startAt: shared start time as seconds since 1970 (time.time()), or None to start
        # with a key press. Set it on both computers to the same value.
        if startAt is not None and (isinstance(startAt, bool) or not isinstance(startAt, (int, float))
                                    or not math.isfinite(startAt)):
            raise ValueError("startAt must be a number of seconds or None, got %r" % (startAt,))
        self.__startAt = None if startAt is None else float(startAt)
        # ˄

    def playVideo(self, clock=None):
        # ˅
        """!
        @brief plays the video frame by frame synchronized with the shared start time or a key press.
        
        The frame comes from the clock, so frames are skipped if processing takes too long. At the end of the video, the frame number wraps around and the video loops. 

        @param clock function giving the time in seconds [s], replaced in tests. 
        @return None 
        @rtype None
        @throws ValueError If processing steps encounter invalid values.
        """
        # clock: function giving the time in seconds, replaced in tests. Default: the system
        # wall clock with a shared start time, otherwise a steady clock started by the key press.
        path = self.__setup.getSourcePath()
        source = VideoSource(path)
        fps = source.getFps()
        frameCount = source.getFrameCount()
        shared = self.__startAt is not None
        if clock is None:
            clock = time.time if shared else time.monotonic
        screens, screenIndex = findProjectorScreens()
        display = Display(screens=screens, screen=screenIndex)
        try:
            # Show the first picture, so the projector is lit while waiting.
            first = self.processFrame(source.frameAt(0))
            display.show(first.getFrame())
            display.setFullscreen(True)
            if shared:
                # Wait for the shared start time. Both computers read the same clock time,
                # so a computer that starts late joins at the right frame, not at frame 0.
                start = self.__startAt
                while clock() < start:
                    if self.__isQuitKey(display.waitKey(10)):
                        return
            else:
                if self.__isQuitKey(display.waitKey(0)):
                    return
                start = clock()
            while True:
                # The frame comes from the clock, so a slow computer skips frames
                # instead of falling behind the other one.
                index = int((clock() - start) * fps) % frameCount
                frame = self.processFrame(source.frameAt(index))
                display.show(frame.getFrame())
                self.__output = frame
                if self.__isQuitKey(display.waitKey(1)):
                    return
        finally:
            display.close()
            source.close()
        # ˄

    def scaleSource(self):
        # ˅
        """!
        @brief Scales the source image or video frame to combined image size using crop or fit modes.
        
        Both modes keep the proportions without stretching. The result is always 2* resX - overlapPx wide and resY high.
        
        @return None
        @rtype None
        """
        if self.__sourceFrame is None:
            raise ValueError("No source frame: call load() first")
        src = self.__sourceFrame.getFrame()
        resX, resY = self.__setup.getProjectorResXY()
        overlapPx = self.__math.overlapPx(
            resX, self.__setup.getImageWidthCm(), self.__setup.getProjectorSpacingCm())
        # Combined image: both projectors side by side, minus the shared overlap.
        dstW, dstH = 2 * resX - overlapPx, resY
        srcH, srcW = src.shape[:2]
        fit = self.__setup.getScaleMode() == "fit"
        if fit:
            # Whole picture visible: scale until it fits inside the target on both sides,
            # then put it in the centre of a black picture of the target size.
            scale = min(dstW / srcW, dstH / srcH)
            newW = min(dstW, max(1, round(srcW * scale)))
            newH = min(dstH, max(1, round(srcH * scale)))
        else:
            # Keep the aspect ratio: scale until the picture covers the target on both
            # sides, then cut the extra from the centre. Nothing is stretched.
            scale = max(dstW / srcW, dstH / srcH)
            newW = max(dstW, math.ceil(srcW * scale - 1e-9))
            newH = max(dstH, math.ceil(srcH * scale - 1e-9))
        # Written once per source size, so a video does not repeat it for every frame.
        if (newW, newH) != (dstW, dstH) and self.__loggedCrop != (srcW, srcH, fit):
            self.__loggedCrop = (srcW, srcH, fit)
            _log.info("Source aspect ratio %.3f differs from target %.3f; %s",
                      srcW / srcH, dstW / dstH,
                      "black bars are added" if fit else "the extra edges are cropped")
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        resized = cv2.resize(src, (newW, newH), interpolation=interpolation)
        if fit:
            canvas = np.zeros((dstH, dstW) + resized.shape[2:], resized.dtype)
            x0 = (dstW - newW) // 2
            y0 = (dstH - newH) // 2
            canvas[y0:y0 + newH, x0:x0 + newW] = resized
            resized = canvas
        else:
            x0 = (newW - dstW) // 2
            y0 = (newH - dstH) // 2
            resized = resized[y0:y0 + dstH, x0:x0 + dstW].copy()
        scaled = Image()
        scaled.setFrame(resized)
        self.__sourceFrame = scaled
        return scaled
        # ˄

    def processFrame(self, array, masked=True):
        # ˅
        """!
        @brief Processes one video frame through scale, crop, and mask to produce this side's picture.
        
        Setting masked to False leaves the mask out, allowing comparison with and without blend.
        
        @param array One video frame (numpy array) [none].
        @param masked masked=False leaves the mask out, to compare with and without the blend [none].
        @return The processed frame as an Image object [none]
        @rtype Image
        """
        # One video frame (numpy array) through scale, crop and mask: gives this side's picture.
        # masked=False leaves the mask out, to compare with and without the blend.
        image = Image()
        image.setFrame(array)
        self.__sourceFrame = image
        self.scaleSource()
        sliceFrame = self.crop()
        return self.applyMask(sliceFrame) if masked else sliceFrame
        # ˄

    @staticmethod
    def __isQuitKey(key):
        # ˅
        """!
        @brief Checks if the provided key code corresponds to a quit action.
        
        True if the key code (low 8 bits) is in QUIT_KEYS; False for -1 (no key).
        
        @param key The key code to check [none]
        @return True if it is a quit key, False otherwise
        @rtype bool
        """
        return key != -1 and (key & 0xFF) in PipelineClass.QUIT_KEYS
        # ˄

    def __init__(self, setup):

        self.__setup = None

        self.__math = None

        self.__sourceFrame = None

        self.__mask = None

        self.__output = None

        self.__startAt = None

        # ˅
        # Not in the diagram: the last source size the crop/fit notice was written for.
        """!
        @var __loggedCrop
        @brief The last source size the crop or fit notice was written for.
        
        It remembers the source size for which the "cropped" or "black bars" message was written so it is only written once.
        """
        self.__loggedCrop = None
        if setup is None or setup.getProjectorResXY() is None:
            raise ValueError("setup must be a loaded SetupClass: call load() and validate() first")
        self.__setup = setup
        self.__math = MathClass()
        resX = setup.getProjectorResXY()[0]
        w = setup.getImageWidthCm()
        d = setup.getProjectorSpacingCm()
        side = setup.getProjectorSide()
        """!
        @var __region
        @brief The strip of the combined image of this computer's side.
        
        It is built once in the constructor.
        """
        self.__region = self.__math.cropRegion(side, resX, w, d)
        overlapPx = self.__math.overlapPx(resX, w, d)
        self.__mask = self.__math.blendMask(overlapPx, resX, side, setup.getBlendCurveGamma())
        # ˄

    # ˅
    
    # ˄


# ˅

# ˄
