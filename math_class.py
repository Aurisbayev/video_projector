#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import math

from mask import Mask
from region import Region
from side import Side


# ˄


class MathClass(object):
    # ˅
    
    # ˄

    @classmethod
    def overlapCm(cls, w, d):
        # ˅
        
        return float(w) - float(d)
        # ˄

    @classmethod
    def totalWidthCm(cls, w, d):
        # ˅
        
        return float(w) + float(d)
        # ˄

    @classmethod
    def pxPerCm(cls, resX, w):
        # ˅
        
        if w <= 0:
            raise ValueError(f"w must be greater than 0, got {w}")
        return float(resX) / float(w)
        # ˄

    @classmethod
    def overlapPx(cls, resX, w, d):
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
