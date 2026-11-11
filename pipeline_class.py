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

    @details Loads thes ource, sclaes it, crops the region for this projector, applies a blending mask, and displays the result. A video goes through the same steps for every frame. 

    """

    # ˅
    
    ## Keys that stop a video: Esc and q.
    QUIT_KEYS = (27, ord("q"))

    # ˄

    def load(self):
        """!
        @brief Loads the source image using the path in the settings.

        @returns The loaded Image object

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
        @brief Extracts the portion of the combined image that belongs to this projector. 
        @details The size is resX x resY

        @returns Image sliceFrame Image slice for this projector. It is a copy, so applyMask() cannot change the source frame.

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
        @brief Applies the blending mask to the cropped image/frame.
        @details Only the columns of the mask fades are calculated; columns with alpha 1 are copied. 

        @param sliceFrame The cropped portion of the frame to be masked.

        @returns Image (a new picture; the input is not changed).

        @throws ValueError if there is no mask or the slice width does not match the mask length..
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
        @brief Opens a window on the selected monitor and displays the processed image.
        @details The screens can only be read on macOS. Elsewhere the system places the window (see findProjectorScreens()).

        @param frame, an Image object containing the final image.

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
        @details A picture is loaded, scaled, cropped, masked and displayeyd. Each computer shows one side.

        If isVideo() is true, it calls playVideo() and ends; otherwise it runs the picture steps.


        @throws FileNotFoundError If the source file does not exist.
        @throws ValueError If the source cannot be read, or a step fails.
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

        @return bool True if sourcePath has a video extension, False otherwise [none].
        """

        # ˅
        
        return VideoSource.isVideoPath(self.__setup.getSourcePath())
        # ˄

    def setStartAt(self, startAt):
        """!
        @brief Sets the shared start time or clears it with None.

        Both computers must be given the same value.

        @param startAt shared start time as seconds since 1970 (like time.time()) [s], or None to start with a key press.
        @return None
        @rtype None
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
        @brief Plays the video frame by frame synchronized with the shared start time or a key press.

        @details The frame comes from the clock, so frames are skipped if processing takes too long. At the end of the video, the frame number wraps around and the video loops.

        The first frame is shown while waiting for the start: the shared time from setStartAt(), or otherwise a key press. 
        Esc or q during the wait stops without playing, and Esc or q stops the video. 
        The window and the video file are closed when playing stops, also after an error.

        With a shared start time, a computer started after that time joins at the frame that belongs to that moment, so two computers with the same clock show the same frame. The last processed frame is kept in output.

        @param clock Function giving the time in seconds [s]. The default is the wall clock (time.time) when a shared start time is set, otherwise a steady clock (time.monotonic). Tests give their own.

        @throws ValueError If processing steps encounter invalid values.
        @throws FileNotFoundError If the video file does not exist.
        @throws ValueError If the video cannot be opened or a frame cannot be read.
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
        @brief Scales the source image or video frame to combined image size using crop or fit modees.

        @details The result is always , 2 * resX - overlapPx by resY. 
        Both modes keep the proportions without stretching.
        "crop" cuts the extra edges and keeps the center.
        "fit" shows the whole picture in the centre with black bars. 
        It writes an INFO message when the aspect ratios differ, once per source size and mode.

        @returns the scaled Image (which replaces the source frame).

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
        @brief Processes one video frame through scale, crop, and mask to produce this side's picture.
        @details The frame replaces the source frame.

        @param array One video frame (numpy array) [none].
        @param masked True applies the mask, False leaves it out, to compare with and without the blend [none].
        @return Image The processed frame as an Image object [none]
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
        @brief Checks if the provided key code corresponds to a quit action.

        @details True if the key code (low 8 bits) is in QUIT_KEYS; False for -1 (no key).
        Only the low 8 bits are compared, because some backends add modifier bits.

        @param key The key code to check [none]
        @return bool True if it is a quit key, False otherwise
        """

        # ˅
        
        return key != -1 and (key & 0xFF) in PipelineClass.QUIT_KEYS
        # ˄

    def __init__(self, setup):
        """!
        @brief Stores settigs and builds the math object, region and mask once.

        @param setup a loaded SetupClass

        @returns Nothing

        @throws ValueError if setup is missing or isn't loaded.
        """


        self.__setup = None

        self.__math = None

        self.__sourceFrame = None

        self.__mask = None

        self.__output = None

        self.__startAt = None

        # ˅
        # Not in the diagram: the last source size the crop/fit notice was written for.
        ## @var __loggedCrop
        #  @brief The last source size the crop or fit notice was written for.
        #
        #  It remembers the source size for which the "cropped" or "black bars" message was written so it is only written once.
        self.__loggedCrop = None
        if setup is None or setup.getProjectorResXY() is None:
            raise ValueError("setup must be a loaded SetupClass: call load() and validate() first")
        self.__setup = setup
        self.__math = MathClass()
        resX = setup.getProjectorResXY()[0]
        w = setup.getImageWidthCm()
        d = setup.getProjectorSpacingCm()
        side = setup.getProjectorSide()
        ## @var __region
        #  @brief The strip of the combined image of this computer's side.
        #
        #  It is built once in the constructor.
        self.__region = self.__math.cropRegion(side, resX, w, d)
        overlapPx = self.__math.overlapPx(resX, w, d)
        self.__mask = self.__math.blendMask(overlapPx, resX, side, setup.getBlendCurveGamma())
        # ˄

    # ˅
    ## @fn __init__(self, setup)
    #  @brief Initializes the pipeline attributes. Builds the math object, the region and
    #         the mask once.
    #
    #  @param setup A loaded SetupClass.
    #  @throws ValueError If setup is missing or not loaded.
    #  @throws ValueError If the settings give an overlap in pixels that is out of range, or
    #          a side or gamma the mask cannot be built from.

    # ˄


# ˅

# ˄
