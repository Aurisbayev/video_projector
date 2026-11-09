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
    @details It converst the physical projector measurements into pixel positions and brightness values.
    @details MathClass stores nothing. All methods belong to the class and are called without an object. Validation is handled by the SetupClass.
    """

    # ˅
    
    # ˄

    @classmethod
    def overlapCm(cls, w, d):
        """!
        @brief Calculates the physical width of the overlapped region.

        @details Width of the overlapped region \f(= w - d\f). 

        @param w Width of the image projected from one projector, in cm.
        @param d Distance between the two projectors in cm.

        @return float Width of the overlapped region in cm.
        """

        # ˅
        
        return float(w) - float(d)
        # ˄

    @classmethod
    def totalWidthCm(cls, w, d):
        """!
        @brief Calculates the total physical width of the whole, combined image on the projection surface.
        @altbrief Calculates the total physical width covered by both projectors.

        @details Width of whole combined image \f(= w + d\f). 

        @param w Width of the image projected from one projector in cm.
        @param d Distance between the two projectors in cm.

        @return float Total combined projection width in cm.
        """

        # ˅
        
        return float(w) + float(d)
        # ˄

    @classmethod
    def pxPerCm(cls, resX, w):
        """!
        @brief Calculates the screen's horizontal pixel density 

        @details Horizontal pixels per centimeter of the screen \f(= resX / w\f). 

        @param resX, the horizontal resolution of one projector in pixels.
        @param w Width of the image projected by one projector in cm.

        @return float horizontal pixel density [px/cm].
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

        @param resX, the horizontal resolution of one projector in pixels.
        @param w Width of the image projected from one projector in cm.
        @param d Distance between the two projectors in cm.

        @return integer Overlap width in whole pixels, rounded half up.
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
        @brief Calculates which portion of the combined image this projector shows.. 

        @details LEFT starts at column 0 and is resX wide. Right starts at column resX - overlapPx and is resX wide.

        @param projectorSide LEFT or RIGHT projector.
        @param resX, the horizontal resolution of one projector in pixels.
        @param w Width of the image projected from one projector in cm.
        @param d Distance between the two projectors in cm.

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
        @brief Generates the fade (brightness multipliers) used to make the overlapping projector images blend together.

        @details The fade's value is 1 outside the overlap. 

        Inside the overlap, with t = (i + 0.5) / overlapPx for overlap column i.

        LEFT is (1-t)^(1/gamma)
        RIGHT is t^(1/gamma)

        With gamma 1, the two sides add up to the full picture.


        @param overlapPx Width of the overlapped region in whole pixels.
        @param resX, the horizontal resolution of one projector in pixels.
        @param projectorSide LEFT or RIGHT projector.
        @param gamma Value controlling the shape of the fade.


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
