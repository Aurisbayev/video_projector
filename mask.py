#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Mask(object):
    """!
    @brief Stores the brightness multipliers used to blend the overlapping projecor images.
    """

    # ˅
    
    # ˄

    def getAlpha(self):
        """!
        @brief Gives the brightness multipliers for this projector.
        @return alpha a list of brightness multipliers (floats between 0 and 1), one for each horizontal pixel column.
        """

        # ˅
        
        return self.__alpha
        # ˄

    def __init__(self, alpha):
        """!
        @brief Initializes the Mask object.
        @param alpha list of floats between 0 and 1, one per pixel column.
        """

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
