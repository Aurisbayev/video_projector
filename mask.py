#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅

# ˄


class Mask(object):
    """!
    @brief Stores the per-column brightness multipliers for one image.

    @details Each alpha value controls the brightness for one horizontal pixel column. 
    Values range from 0.0 (black) to 1.0 (unchanged brightness). The values are used to blend the overlapping areas of the two projected images.
    
    @par Class Attributes:
    alpha [double] List of floating-point brightness multipliers (Between 0.0 and 1.0), one per horizontal pixel column.
    """

    # ˅
    
    # ˄

    def getAlpha(self):
        """!
        @brief Returns the brightness multipliers stored in this mask.

        @return alpha [double], List of floating-point brightness multipliers (Between 0.0 and 1.0), one per horizontal pixel column.
        """

        # ˅
        
        return self.__alpha
        # ˄

    def __init__(self, alpha):
        """!
        @brief Initializes the Mask object with the supplied alpha.

        @param alpha [double], List of floating-point brightness multipliers (Between 0.0 and 1.0), one per horizontal pixel column.
        """

        self.__alpha = None

        # ˅
        self.__alpha = alpha
        # ˄

    # ˅
    # ˄


# ˅

# ˄
