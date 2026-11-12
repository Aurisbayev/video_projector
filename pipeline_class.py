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
    """!
    @brief Processes an image or video for projection.

    @details Loads the source, scales it, crops the region for this projector, applies a blending mask, and displays the result. A video goes through the same steps for every frame. 

    @par Class Attributes:
    setup [SetupClass], Contains the information from the settings file.\n
    math [MathClass], The class used for calculations.\n
    sourceFrame [Image], Holds the source image (after load()) and later the scaled combined frame (after scaleSource()). \n 
    mask [Mask], Contains this projector's per-column brightness multipliers. Built once in the constructor. \n
    output [Image], Contains the most recently displayed/processed output frame.\n
    startAt [double], Optional shared video start time as seconds.\n
    region [Region], Contains the horizontal crop for this projector. \n
    """

    # ˅
    
    ## Keys that stop a video: Esc and q.
    QUIT_KEYS = (27, ord("q"))

    # ˄

    def load(self):
        """!
        @brief Loads the source image into an Image object.

        @returns [Image] The loaded Image object.

        @throws FileNotFoundError if the path is wrong. 
        @throws ValueError if the file is not a readable picture.
        """

        # ˅
        
        # Image.load() raises FileNotFoundError / ValueError naming the path.
        path = self.__setup.getSourcePath()
        image = Image()
        image.load(path)
        self.__sourceFrame = image
        return image
        # ˄

    def crop(self):
        """!
        @brief Extracts this projector's region from the scaled, combined image.
        @details The crop's size is resX x resY.

        @returns [Image] A new Image containing this projector's cropped region. It is a copy, so applyMask() cannot change the source frame.

        @throws ValueError if there is no source or the region does not fit.
        """

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
        """!
        @brief Applies the projector's blending mask to the cropped frame.

        @details The mask supplies one alpha per horiztonal column. 
        Columns with alpha 1.0 are copied unchanged, the other columns are multiplied by alpha. 
        The input image is not modified.

        @param sliceFrame [Image], This projector's cropped frame.

        @returns Image (a new picture; the input is not modified).

        @throws ValueError if there is no mask or the frame width differs from the mask length.
        """

        # ˅
        
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
        """!
        @brief Displays the processed Image from applyMask() on the selected monitor.

        @details Detects connected monitors and retrieves their positions and
        dimensions on mac)S. On other systems, the operating
        system determines the window position. 
        (See display.py findProjectorScreens()).

        @param frame [Image] Object containing the final image with the mask.

        @throws ValueError if frame is not an Image or is empty.
        """

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
        """!
        @brief Executes the pipeline processing.

        @details For a still image, loads, scales, crops, masks and displays. 
        For a video, calls playVideo().

        @return None.

        @throws FileNotFoundError If the source file does not exist.
        @throws ValueError If the source cannot be read or a step fails.
        """

        # ˅
        
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
        """!
        @brief Checks if the source path has a video extension.
        @details Only the file extension is checked (see VideoSource.isVideoPath()).

        @return [bool] True if sourcePath has a video extension, False otherwise [none].
        """

        # ˅
        
        return VideoSource.isVideoPath(self.__setup.getSourcePath())
        # ˄

    def setStartAt(self, startAt):
        """!
        @brief Sets or clears the shared start time.

        @details Both computers must be given the same value, so their video frames are synchronized.

        @param startAt [double], shared start time as seconds since Unix epoch or None to wait for a key press before playback.
        @return None.

        @throws ValueError If the value is not a finite number or None, including True, False and text such as "14:30" (convert text with parseStartTime() first).
        """

        # ˅
        
        if startAt is not None and (isinstance(startAt, bool) or not isinstance(startAt, (int, float))
                                    or not math.isfinite(startAt)):
            raise ValueError("startAt must be a number of seconds or None, got %r" % (startAt,))
        self.__startAt = None if startAt is None else float(startAt)
        # ˄

    def playVideo(self, clock=None):
        """!
        @brief Plays the video, frame by frame, synchronized with the shared start time or a key press.

        @details The frame comes from the clock, so frames are skipped if processing takes too long. At the end of the video, the frame number wraps around and the video loops.

        The first frame is shown while waiting to start. With a shared start time, the frame index is calculated from the clock, 
        so a computer joining late can display the frame corresponding to the shared time. Processing delays cause
        frames to be skipped rather than allowing playback to fall behind. Playback loops at the end of the video. 
        The display window and video capture are closed when playback ends or an error occurs.

        @param clock [function] Optional function giving the time in seconds. Defaults to the wall clock (time.time) when a shared start time is set, otherwise a steady clock (time.monotonic). When testing, supply own clock function.
        
        @return None.
        """

        # ˅
        
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
        """!
        @brief Scales the source frame to combined image dimensions using either crop or fit modes.

        @details The combined image dimensions are (2 * resX - overlapPx) by resY. 
        
        Both modes keep the proportions without stretching.
        In crop mode, the image fills the target and extra edges are removed.
        In fit mode, the complete image is fitten inside the targe, and unused areas are filled with black.
        It writes an INFO message when the aspect ratios differ, once per source size and mode.
        The scaled result replaced sourceFrame.

        @returns [Image] the scaled combined image.

        @throws ValueError if load() was not called.
        """

        # ˅
        
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
        """!
        @brief Processes one video frame for this projector. 
        
        @details The supplied array replaces the source frame. Then, scales, crops and optionally applies the blending masks it.

        @param array [ndarray] Video frame pixel data.
        @param masked [bool] If True, applies the mask; if False, return the unmasked crop.
        @return [Image] The processed frame wrapped in an Image object
        @throws ValueError If array is not a NumPy array, or scaling, cropping or masking fails.
        """

        # ˅
        
        image = Image()
        image.setFrame(array)
        self.__sourceFrame = image
        self.scaleSource()
        sliceFrame = self.crop()
        return self.applyMask(sliceFrame) if masked else sliceFrame
        # ˄

    @staticmethod
    def __isQuitKey(key):
        """!
        @brief Checks whether an OpenCV key code requests playback to stop.

        @details True if the key code (low 8 bits) is in QUIT_KEYS; False for -1 (no key).
        Only the low 8 bits are compared, because some backends add modifier bits.

        @param key [int] The key code to check.
        @return [bool] True for a quit key (q or Esc); otherwise False.
        """

        # ˅
        
        return key != -1 and (key & 0xFF) in PipelineClass.QUIT_KEYS
        # ˄

    def __init__(self, setup):
        """!
        @brief Stores settigs and builds the math object, region and mask once.

        @param setup a loaded SetupClass.

        @throws ValueError if setup is missing or isn't loaded.
        """


        self.__setup = None

        self.__math = None

        self.__sourceFrame = None

        self.__mask = None

        self.__output = None

        self.__startAt = None

        # ˅
        self.__loggedCrop = None
        if setup is None or setup.getProjectorResXY() is None:
            raise ValueError("setup must be a loaded SetupClass: call load() and validate() first")
        self.__setup = setup
        self.__math = MathClass()
        resX = setup.getProjectorResXY()[0]
        w = setup.getImageWidthCm()
        d = setup.getProjectorSpacingCm()
        side = setup.getProjectorSide()
        self.__region = self.__math.cropRegion(side, resX, w, d)
        overlapPx = self.__math.overlapPx(resX, w, d)
        self.__mask = self.__math.blendMask(overlapPx, resX, side, setup.getBlendCurveGamma())
        # ˄

    # ˅
    # ˄


# ˅

# ˄
