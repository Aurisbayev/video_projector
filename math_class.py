#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import math

from mask import Mask
from region import Region
from side import Side


# ˄


class MathClass(object):
    """!
    @brief Performs the mathematical calculations for the dual-projector system.

    @details Converts the physical measurements into pixel dimensions, calculates the crop region and the brightness mask.
    MathClass stores nothing. All methods belong to the class and are called without an object. Validation is handled by SetupClass.
    """

    # ˅
    
    # ˄

    @classmethod
    def overlapCm(cls, w, d):
        """!
        @brief Calculates the physical width of the overlapped region.

        @details Width of the overlapped region \f(= w - d\f). 

        @param w [double], Width of the image projected from one projector, in cm.
        @param d [double], Distance between the two projectors, in cm.

        @return double, Physical width of the overlapped region in cm.
        """

        # ˅
        
        return float(w) - float(d)
        # ˄

    @classmethod
    def totalWidthCm(cls, w, d):
        """!
        @brief Calculates the physical width of the combined projected image .

        @details The combined width is \f(= w + d\f). 

        @param w [double], Width of the image projected from one projector, in cm.
        @param d [double], Distance between the two projectors, in cm.

        @return double, Total physical width covered by the combined image in cm.
        """

        # ˅
        
        return float(w) + float(d)
        # ˄

    @classmethod
    def pxPerCm(cls, resX, w):
        """!
        @brief Calculates the horizontal pixel density of one projector. (Should be the same for both projectors.) 

        @details Horizontal pixels per centimeter of the screen \f(= resX / w\f). 

        @param resX [int], The horizontal resolution of one projector, in pixels.
        @param w [double], Width of the image projected from one projector, in cm.

        @return double, Horizontal pixel density, in pixels per cm.
        @throws ValueError if w is not greater than 0.
        """

        # ˅
        
        if w <= 0:
            raise ValueError(f"w must be greater than 0, got {w}")
        return float(resX) / float(w)
        # ˄

    @classmethod
    def overlapPx(cls, resX, w, d):
        """!
        @brief Calculates overlapped region's width in whole pixels

        @details floor((w - d) * (resX / w) + 0.5). 

        @param resX [int], The horizontal resolution of one projector, in pixels.
        @param w [double], Width of the image projected from one projector, in cm.
        @param d [double], Distance between the two projectors, in cm.

        @return integer, Overlap width in whole pixels, rounded half up.
        @throws ValueEror If the rounded overlap is outside the valid pixel range.
        """

        # ˅
        
        # Round half up (not Python round(), which rounds halves to even).
        # This is the only place the overlap is rounded, so both computers agree.
        px = math.floor(cls.overlapCm(w, d) * cls.pxPerCm(resX, w) + 0.5)
        if px < 1 or px >= resX:
            raise ValueError(f"overlapPx must be in [1, resX), got {px} (resX={resX})")
        return int(px)
        # ˄

    @classmethod
    def cropRegion(cls, projectorSide, resX, w, d):
        """!
        @brief Calculates the section of the combined image display by this projector.

        @details The LEFT projector starts at column 0 and is resX wide. The RIGHT projector starts at column resX - overlapPx and is resX wide.

        @param projectorSide [Side], The LEFT or RIGHT projector.
        @param resX [int], The horizontal resolution of one projector, in pixels.
        @param w [double], Width of the image projected from one projector, in cm.
        @param d [double], Distance between the two projectors, in cm.

        @return Region The portion of the combined image displayed by this projector.
        """
        
        # ˅
        
        if not isinstance(projectorSide, Side):
            raise ValueError(f"projectorSide must be a Side, got {projectorSide!r}")
        overlap = cls.overlapPx(resX, w, d)
        if projectorSide is Side.LEFT:
            return Region(0, resX)
        return Region(resX - overlap, resX)
        # ˄

    @classmethod
    def blendMask(cls, overlapPx, resX, projectorSide, gamma):
        """!
        @brief Creates the alpha mask (the brightness multipliers) for one projector.

        @details Columns outside the overlap have alpha 1.0.

        Inside the overlap, each overlap column i uses the centre position t = (i + 0.5) / overlapPx.

        The LEFT fade is (1-t)^(1/gamma).
        The RIGHT fade is t^(1/gamma).

        With gamma 1.0, the two sides add up to the full picture.


        @param overlapPx, Width of the overlap, in pixels.
        @param resX [int], The horizontal resolution of one projector, in pixels.
        @param projectorSide [Side], The LEFT or RIGHT projector.
        @param gamma [double], Value controlling the shape of the fade.



        @return Mask Blending mask containing brightness multipliers from 0 to 1 for this computer's image.
        """

        # ˅
        
        if not isinstance(projectorSide, Side):
            raise ValueError(f"projectorSide must be a Side, got {projectorSide!r}")
        if not 0 < overlapPx < resX:
            raise ValueError(f"overlapPx must satisfy 0 < overlapPx < resX, got {overlapPx}")
        if gamma <= 0:
            raise ValueError(f"gamma must be greater than 0, got {gamma}")
        # t is the centre of overlap column i, as a fraction of the overlap.
        ts = [(i + 0.5) / overlapPx for i in range(overlapPx)]
        if projectorSide is Side.LEFT:
            fade = [(1.0 - t) ** (1.0 / gamma) for t in ts]
            alpha = [1.0] * (resX - overlapPx) + fade
        else:
            fade = [t ** (1.0 / gamma) for t in ts]
            alpha = fade + [1.0] * (resX - overlapPx)
        return Mask(alpha)
        # ˄

    # ˅
    
    # ˄


# ˅

# ˄
