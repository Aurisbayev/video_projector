#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Region(object):
    """!
    @brief Represents a horizontal section of the combined image that a particular that this projector shows. 

    @details
    \par Class Attributes:
    xStartPx Starting horizontal pixel position.\n
    widthPx Width of the region in pixels.

    @details
    """

    # ˅
    
    # ˄

    def getXStartPx(self):
        """!
        @brief Returns the starting column for the region.

        @return integer representing the starting column.
        """

        # ˅
        
        return self.__xStartPx
        # ˄

    def getWidthPx(self):
        """!
        @brief Returns the region's width.

        @return integer representing the region's width.
        """

        # ˅
        
        return self.__widthPx
        # ˄

    def __init__(self, xStartPx, widthPx):
        """!
        @brief Initializes the Region object.

        @param xStartPx Starting horizontal pixel position.
        @param widthPx Width of the region in pixels.
        """


        self.__xStartPx = None

        self.__widthPx = None

        # ˅
        self.__xStartPx = xStartPx
        self.__widthPx = widthPx
        # ˄

    # ˅
    # ˄


# ˅

# ˄
