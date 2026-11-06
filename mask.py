#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Mask(object):
    # ˅
    """!
    @brief The brightness multipliers for one projector
    """
    # ˄

    def getAlpha(self):
        # ˅
        """!
        @brief Gives the brightness multipliers for the projector.

        @return List of floats between 0 and 1, one per pixel column.
        @rtype list
        """
        return self.__alpha
        # ˄

    def __init__(self, alpha):

        self.__alpha = None

        # ˅
        self.__alpha = alpha
        # ˄

    # ˅
    ## @fn __init__(self, alpha)
    #  @brief Initializes the Mask instance.
    #
    #  @param alpha List of floats between 0 and 1, one per pixel column.

    # ˄


# ˅

# ˄
