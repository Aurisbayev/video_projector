#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Region(object):
    # ˅
    """!
    @brief A strip of the combined image that one projector shows
    """
    # ˄

    def getXStartPx(self):
        # ˅
        """!
        @brief Gives the first pixel column of the region.

        @return First column of the region in the combined image [px].
        @rtype int
        """
        return self.__xStartPx
        # ˄

    def getWidthPx(self):
        # ˅
        """!
        @brief Gives the width of the region.

        @return Number of pixel columns in the region [px].
        @rtype int
        """
        return self.__widthPx
        # ˄

    def __init__(self, xStartPx, widthPx):

        self.__xStartPx = None

        self.__widthPx = None

        # ˅
        self.__xStartPx = xStartPx
        self.__widthPx = widthPx
        # ˄

    # ˅
    ## @fn __init__(self, xStartPx, widthPx)
    #  @brief Initializes the Region instance.
    #
    #  @param xStartPx First column [px].
    #  @param widthPx Number of columns [px].

    # ˄


# ˅

# ˄
