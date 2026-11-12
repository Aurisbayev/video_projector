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
    @brief Loads, validates, stores, and provides access to projection settings.

    @details Settings are read from a JSON file. The required values describe the
    projector resolution, projected image width, projector spacing, blend gamma,
    source path, and projector side. The optional scaleMode setting defaults to
    "crop"; supported modes are "crop" and "fit".

    @par Class Attributes: 
    projectorResXY: [int] Projection resolution as a list in the form (horizontal width, vertical height), in pixels.\n
    imageWidthCm: [double], Physical width of the image projected by one projector in cm.\n
    projectorSpacing: [double], Physical distance between the two projectors.\n
    blendCurveGamma: [double], Positive value controlling the overlap fade shape.\n
    sourcePath: [string], Path of the source image or video.\n
    projectorSide: [Side] Identifies the projector controlled by this computer (Side.LEFT or Side.RIGHT).\n
    scaleMode: [string] Source scaling mode: "crop" (default) or "fit". Explains how the source is fitted to the combined image: crop fills it and cuts the edges, fit shows the whole source with black bars.
    """

    # ˅
    
    # ˄

    def load(self, path):
        """!
        @brief Reads the JSON settings file and stores its values in this object.

        @details Relative sourcePath values are resolved relative to the directory
        containing the settings file. If scaleMode is absent, the default "crop" is used.

        @param path [string] Path to the JSON settings file.
        @return None.
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
        @brief Validates the loaded settings. If not, writes the failure reason to the log.

        @details Checks the following:
                The resolution is two positive integers.
                w and d are positive numbers.
                d is smaller than w.
                gamma is inside the allowed range (0.5 to 3.0).
                The source picture exists.
                The side is LEFT or RIGHT.
                scaleMode is supported.

        @returns [bool] True when all checks pass; otherwise False.
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
        @brief Returns the configured projector resolution.

        @returns list [int] A copy of (horizontal resolution, vertical resolution) in pixels 
        or None if settings have not been loaded.
        """

        # ˅
        
        return list(self.__projectorResXY) if self.__projectorResXY is not None else None
        # ˄

    def getImageWidthCm(self):
        """!
        @brief Returns the physical projected image width for one projector.

        @returns [double] Image width in cm.
        """

        # ˅
        
        return self.__imageWidthCm
        # ˄

    def getProjectorSpacingCm(self):
        """!
        @brief Returns the physical distance between the two projectors.

        @returns [double] Projector spacing in cm. 
        """

        # ˅
        
        return self.__projectorSpacingCm
        # ˄

    def getBlendCurveGamma(self):
        """!
        @brief Returns the gamma value used to shape the overlap blend curve.

        @returns [double] Blend-curve gamma.
        """

        # ˅
        
        return self.__blendCurveGamma
        # ˄

    def getSourcePath(self):
        """!
        @brief Returns the path of the source image or video.

        @returns [string] Source file path.
        """

        # ˅
        
        return self.__sourcePath
        # ˄

    def getProjectorSide(self):
        """!
        @brief Gives which projector this computer drives.

        @returns projectorSide.
        """

        # ˅
        
        return self.__projectorSide
        # ˄

    def getScaleMode(self):
        """!
        @brief Returns the mode used to fit the source into the combined image.

        @details Has it been cropped or fitted?

        @returns [string] "crop" or "fit".
        """

        # ˅
        
        return self.__scaleMode
        # ˄

    def __init__(self):

        """!
        @brief Creates an empty settings object.
        @details The default scale mode is "crop"; other settings are populated by load().
        """

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
        @brief Replaces configured scaleMode.
        @param mode [string] "crop" or "fit".
        @return None.
        """

        
        self.__scaleMode = self.__toScaleMode(mode)

    def setProjectorSide(self, side):
        """!
        @brief Replaces the projector side loaded from the settings file.

        @param side [Side], Side.LEFT or Side.RIGHT.

        @return None.

        @throws ValueError if side is not a Side.
        """

        
        if not isinstance(side, Side):
            raise ValueError("side must be a Side, got %r" % (side,))
        self.__projectorSide = side
    # ˄


# ˅

# ˄
