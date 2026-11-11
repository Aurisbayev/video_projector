#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
from enum import Enum


# ˄


class Side(Enum):
    """!
    @brief Identifies which projector is controlled by a computer in the dual projector system.
    
    @details The two values distinguish the left and right projector. They are used 
    when calculating the crop region and the overlap brightness mask.
    """

    ## Left projector, represented by the value 1 
    LEFT = 1 

    ## Right projector, represented by the value 2
    RIGHT = 2 


# ˅
# ˄
