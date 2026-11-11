#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Region(object):
    """!
    @brief Represents the horizontal pixel region of the combined image showned by one projector. 

    @details
    \par Class Attributes:
    xStartPx [int], First horizontal pixel column in the region.\n
    widthPx [int], Number of horizontal pixel columns in the region.
    """

    # ˅
    
    # ˄

    def getXStartPx(self):
        """!
        @brief Returns the starting column for the region.

        @return [integer], Starting column index, measured from the left edge of the combined image.
        """

        # ˅
        
        return self.__xStartPx
        # ˄

    def getWidthPx(self):
        """!
        @brief Returns the horizontal width of this region.

        @return [integer], Number of pixel columns in this region.
        """

        # ˅
        
        return self.__widthPx
        # ˄

    def __init__(self, xStartPx, widthPx):
        """!
        @brief Initializes the Region object.

        @param xStartPx [int], Index of the first horizontal pixel column.
        @param widthPx [int], Number of columns included in the region.
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
