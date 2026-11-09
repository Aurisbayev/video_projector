#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Region(object):
    # ˅
    
    # ˄

    def getXStartPx(self):
        # ˅
        
        return self.__xStartPx
        # ˄

    def getWidthPx(self):
        # ˅
        
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
