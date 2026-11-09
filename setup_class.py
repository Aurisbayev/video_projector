#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import json
import logging
import math
import os

from side import Side

_log = logging.getLogger(__name__)

_KEY_RES = "projectorResXY"
_KEY_WIDTH = "imageWidthCm"
_KEY_SPACING = "projectorSpacingCm"
_KEY_GAMMA = "blendCurveGamma"
_GAMMA_MIN = 0.5   # placeholder, not decided
_GAMMA_MAX = 3.0   # placeholder, not decided
_KEY_SOURCE = "sourcePath"
_KEY_SIDE = "projectorSide"
_KEY_SCALE = "scaleMode"
## The allowed values of scaleMode. The default is crop.
SCALE_MODES = ("crop", "fit")   # crop: fill and cut the edges, fit: whole picture with black bars
_DEFAULT_SCALE = "crop"
# ˄


class SetupClass(object):
    """!
    @brief Reads and stores the values from the settings file, validating and providing access to them.

    @details 

    @var projectorResXY A list of two integers The projector's resolution as width and height in pixels
    @var imageWidthCm w The width of the image projected from one projector in cm.
    @var projectorSpacing d The physical distance between each projector.
    @var blendCurveGamma Gamma that shapes the fade in the overalp.
    @var sourcePath A string containing the image-file path
    @var projectorSide LEFT or RIGHT projector.
    @var scaleMode crop (default) or fit. Explains how the source is fitted to the combined image: crop fills it and cuts the edges, fit shows the whole source with black bars.
    """

    # ˅
    
    # ˄

    def load(self, path):
        """!
        @brief Reads the settings file and stores its values in the object.

        @details

        @param path A string containing the location of the settings file.

        @throws FileNotFoundError if the file does not exist. 
        @throws ValueError if it is not valid JSON, is not a JSON object, lacks a setting, or a setting has the wrong type. The message names the setting.
        """

        # ˅
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Settings file not found: '%s'" % path)
        except json.JSONDecodeError as e:
            raise ValueError("Settings file '%s' is not valid JSON: %s" % (path, e))

        if not isinstance(data, dict):
            raise ValueError("Settings file '%s' must contain a JSON object at the top level" % path)

        for key in (_KEY_RES, _KEY_WIDTH, _KEY_SPACING, _KEY_GAMMA, _KEY_SOURCE, _KEY_SIDE):
            if key not in data:
                raise ValueError("Missing setting '%s' in '%s'" % (key, path))

        res = self.__toResolution(data[_KEY_RES])
        width = self.__toFloat(_KEY_WIDTH, data[_KEY_WIDTH])
        spacing = self.__toFloat(_KEY_SPACING, data[_KEY_SPACING])
        gamma = self.__toFloat(_KEY_GAMMA, data[_KEY_GAMMA])
        source = data[_KEY_SOURCE]
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Setting '%s' must be a non-empty string (file path), got %r" % (_KEY_SOURCE, source))
        source = os.path.expanduser(source)
        if not os.path.isabs(source):
            source = os.path.join(os.path.dirname(os.path.abspath(path)), source)
        side = self.__toSide(data[_KEY_SIDE])
        # Optional, so settings files from before scaleMode still load.
        scaleMode = self.__toScaleMode(data.get(_KEY_SCALE, _DEFAULT_SCALE))

        self.__scaleMode = scaleMode
        self.__projectorResXY = res
        self.__imageWidthCm = width
        self.__projectorSpacingCm = spacing
        self.__blendCurveGamma = gamma
        self.__sourcePath = source
        self.__projectorSide = side
        # ˄

    def validate(self):
        """!
        @brief Validates the loaded settings. If not, writes the reason to the log.

        @details Checks the following:
                The resolution is two positive integers.
                w and d are positive numbers.
                d is smaller than w.
                gamma is inside the allowed range (0.5 to 3.0).
                The source picture exists.
                The side is LEFT or RIGHT.

        @returns bool True if all checks pass, otherwise False.
        """

        # ˅
        
        res = self.__projectorResXY
        if (not isinstance(res, list) or len(res) != 2
                or not all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in res)):
            return self.__fail("%s must be two positive integers [width, height] in px, got %r" % (_KEY_RES, res))

        w = self.__imageWidthCm
        if not self.__isPositiveNumber(w):
            return self.__fail("%s must be a positive number (cm), got %r" % (_KEY_WIDTH, w))

        d = self.__projectorSpacingCm
        if not self.__isPositiveNumber(d):
            return self.__fail("%s must be a positive number (cm), got %r" % (_KEY_SPACING, d))

        if d >= w:
            return self.__fail("%s (%s cm) must be smaller than %s (%s cm), otherwise the projectors do not overlap"
                               % (_KEY_SPACING, d, _KEY_WIDTH, w))

        g = self.__blendCurveGamma
        if not self.__isPositiveNumber(g) or not (_GAMMA_MIN <= g <= _GAMMA_MAX):
            return self.__fail("%s must be between %s and %s, got %r" % (_KEY_GAMMA, _GAMMA_MIN, _GAMMA_MAX, g))
        
        src = self.__sourcePath
        if not isinstance(src, str) or not src.strip():
            return self.__fail("%s must be a non-empty path, got %r" % (_KEY_SOURCE, src))
        if not os.path.isfile(src):
            return self.__fail("Source image not found: '%s'" % src)

        if not isinstance(self.__projectorSide, Side):
            return self.__fail("%s must be LEFT or RIGHT, got %r" % (_KEY_SIDE, self.__projectorSide))

        if self.__scaleMode not in SCALE_MODES:
            return self.__fail("%s must be one of %s, got %r" % (_KEY_SCALE, ", ".join(SCALE_MODES), self.__scaleMode))

        return True
        # ˄

    def getProjectorResXY(self):
        """!
        @brief Gives the projector resolution.

        @returns ProjectResXY A list of two integers (resX, resY) in pixels.
        """

        # ˅
        
        return list(self.__projectorResXY) if self.__projectorResXY is not None else None
        # ˄

    def getImageWidthCm(self):
        """!
        @brief Gives the width of the projected image from one projector in cm.

        @returns float imageWidthCm.
        """

        # ˅
        
        return self.__imageWidthCm
        # ˄

    def getProjectorSpacingCm(self):
        """!
        @brief Gives the distance between the two projectors in cm.

        @returns float ProjectorSpacingCm.
        """

        # ˅
        
        return self.__projectorSpacingCm
        # ˄

    def getBlendCurveGamma(self):
        """!
        @brief Gives the gamma that shapes blend curve.

        @returns float BlendeCurveGamma.
        """

        # ˅
        
        return self.__blendCurveGamma
        # ˄

    def getSourcePath(self):
        """!
        @brief Gives the path of the source-image (the image to be projected).

        @returns string SourcePath.
        """

        # ˅
        
        return self.__sourcePath
        # ˄

    def getProjectorSide(self):
        """!
        @brief Gives which projector this computer drives.

        @returns Side projectorSide.
        """

        # ˅
        
        return self.__projectorSide
        # ˄

    def getScaleMode(self):
        """!
        @brief Gives how the source is fitted to the combined image.

        @details Has it been cropped or fitted?

        @returns string the value of scaleMode: crop or fit.
        """

        # ˅
        
        return self.__scaleMode
        # ˄

    def __init__(self):

        self.__projectorResXY = None

        self.__imageWidthCm = None

        self.__projectorSpacingCm = None

        self.__blendCurveGamma = None

        self.__sourcePath = None

        self.__projectorSide = None

        self.__scaleMode = _DEFAULT_SCALE

        # ˅
        pass
        # ˄

    # ˅
    ## @fn __init__(self)
    #  @brief Creates an empty setup: scaleMode is crop and every other setting is None
    #         until load().

    @staticmethod
    def __isPositiveNumber(value):
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and value > 0)

    @staticmethod
    def __fail(message):
        _log.error("Invalid settings: %s", message)
        return False

    @staticmethod
    def __toFloat(name, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Setting '%s' must be a number, got %r" % (name, value))
        return float(value)

    @staticmethod
    def __toResolution(value):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Setting '%s' must be a list of two integers [width, height], got %r"
                             % (_KEY_RES, value))
        out = []
        for v in value:
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError("Setting '%s' must contain integers, got %r" % (_KEY_RES, value))
            out.append(v)
        return out

    @staticmethod
    def __toSide(value):
        if isinstance(value, str) and value.strip().upper() in Side.__members__:
            return Side[value.strip().upper()]
        if isinstance(value, int) and not isinstance(value, bool):
            try:
                return Side(value)
            except ValueError:
                pass
        raise ValueError("Setting '%s' must be LEFT or RIGHT (or 1 / 2), got %r" % (_KEY_SIDE, value))

    @staticmethod
    def __toScaleMode(value):
        if isinstance(value, str) and value.strip().lower() in SCALE_MODES:
            return value.strip().lower()
        raise ValueError("Setting '%s' must be one of %s, got %r" % (_KEY_SCALE, ", ".join(SCALE_MODES), value))

    def setScaleMode(self, mode):
        """!
        @brief Replaces scaleMode.
        @details
        @param mode crop or fit.
        @return 
        @throws ValueError if mode is anything else.
        """

        
        self.__scaleMode = self.__toScaleMode(mode)

    def setProjectorSide(self, side):
        """!
        @brief Replaces the side loaded from the settings file.

        @param side Side.LEFT or Side.RIGHT.

        @throws ValueError if side is not a Side.
        """

        
        if not isinstance(side, Side):
            raise ValueError("side must be a Side, got %r" % (side,))
        self.__projectorSide = side
    # ˄


# ˅

# ˄
