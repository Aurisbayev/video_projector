#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import cv2
import numpy as np
# ˄

class Display(object):
    """!
    @brief Manages a window used to display the processed image or video on a selected monitor. 

    @details The window can be moved to a configured monitor and displayed in normal or fullscreen mode.
    @par Class Attributes:
    windowName [string], Name of the window.\n
    screens [integer], List of target monitors as (x, y, width height) in pixels.\n
    screen [integer], Index of the selected monitor, 0 is the primary monitor.\n
    fullscreen [boolean], Whether fullscreen mode is enabled.\n
    windowOpen [boolean], Whether the window has been created.\n
    placedScreen [int], Index of the monitor on which the window was most recently placed.

    """

    # ˅
    
    # ˄

    def setScreen(self, index):
        """!
        @brief Selects which monitor should display the window. 
        @details The method does not immediately move the window to the selected monitor. That is only done when show() is called.

        @param index [int], Index of the target monitor in screens.

        @throws IndexError if screens is not set or the index is out of range.
        """

        # ˅
        
        self.__screen = self.__resolveIndex(index)
        # ˄

    def setFullscreen(self, enabled=True):
        """!
        @brief Set's window's fullscreen state.
        @details Applies it immediately if a window exists. 

        @param enabled [bool], True enables fullscreen; False enables normal window mode.Defaults to True.

        @throws RuntimeError if the window has not been created yet.
        """

        # ˅
        
        if not self.__windowOpen:
            raise RuntimeError(
                "setFullscreen() requires an open window: call show() first "
                f"(window '{self.__windowName}' does not exist yet)"
            )
        self.__fullscreen = bool(enabled)
        cv2.setWindowProperty(
            self.__windowName,
            cv2.WND_PROP_FULLSCREEN,
            Display.__windowMode(self.__fullscreen),
        )
        # ˄

    def isFullscreen(self):
        """!
        @brief Returns whether fullscreen mode is enabled.

        @returns [bool], True when fullscreen mode is enabled; otherwise False.
        """

        # ˅
        
        return self.__fullscreen
        # ˄

    @staticmethod
    def buildTestImage(width=1280, height=720):
        """!
        @brief Creates a test image for checking a projector.
        @details The frame has (BGR) color bars, a checker pattern and text.

        @param width [int], Width of the frame in pixels.
        @param height [int], Height of the frame in pixels.

        @returns frame [ndarray], Test image with shape (height, width, 3) and uint8 pixels.
        """

        # ˅
        
        upperHeight = height // 2
        lowerHeight = height - upperHeight

        bars = np.zeros((upperHeight, width, 3), dtype=np.uint8)
        colours = [
            (255, 255, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0),
            (255, 0, 255), (0, 0, 255), (255, 0, 0), (0, 0, 0),
        ]
        barWidth = width // len(colours)
        for i, colour in enumerate(colours):
            bars[:, i * barWidth:(i + 1) * barWidth] = colour

        cell = 80
        yy, xx = np.indices((lowerHeight, width))
        checker = (((yy // cell) + (xx // cell)) % 2 * 200 + 20).astype(np.uint8)
        lower = np.dstack([checker, checker, checker])

        frame = np.vstack([bars, lower])
        cv2.putText(frame, "PBL4 TEST", (40, upperHeight + lowerHeight // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, "PBL4 TEST", (40, upperHeight + lowerHeight // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 2, cv2.LINE_AA)
        return frame
        # ˄

    def show(self, frame):
        """!
        @brief Displays an image in the window. 

        @details The first call creates the window and moves it to the chosen monitor.

        @param frame [ndarray], Contains the image to display.

        @throws ValueError If frame is not a NumPy array.
        """

        # ˅
        
        if not isinstance(frame, np.ndarray):
            raise ValueError(
                f"frame must be a numpy.ndarray, got {type(frame).__name__}"
            )
        # Placing the window is slow, so it is done only for a new window or a new screen.
        # This keeps show() fast enough to be called for every frame of a video.
        newWindow = not self.__windowOpen
        if newWindow:
            cv2.namedWindow(self.__windowName, cv2.WINDOW_NORMAL)
            self.__windowOpen = True
        if self.__screens is not None and (newWindow or self.__placedScreen != self.__screen):
            x, y, width, height = self.__screens[self.__screen]
            cv2.moveWindow(self.__windowName, x, y)
            cv2.resizeWindow(self.__windowName, width, height)
            self.__placedScreen = self.__screen
        if newWindow:
            cv2.setWindowProperty(
                self.__windowName,
                cv2.WND_PROP_FULLSCREEN,
                Display.__windowMode(self.__fullscreen),
            )
        cv2.imshow(self.__windowName, frame)
        # ˄

    def waitKey(self, delayMs=0):
        """!
        @brief Waits for a key press.

        @param delayMS [int], The waiting time in milliseconds. If set to 0, waits indefinitely.

        @return The key code of the pressed key [int], or -1 if no key was pressed during the waiting time.
        """

        # ˅
        
        return cv2.waitKey(delayMs)
        # ˄

    def close(self):
        """!
        @brief Closes the window. 
        @return None.
        """
        # ˅
        
        if not self.__windowOpen:
            return
        cv2.destroyWindow(self.__windowName)
        self.__windowOpen = False
        # ˄

    def __init__(self, windowName="projector", screens=None, screen=0):
        """!
        @brief Initializes the display settings without opening a window. 

        @param windowName [string], Name of the window.\n
        @param screens [integer], List of target monitors as (x, y, width height) in pixels. If None, the system places the window.
        @param screen [integer], Index of the selected monitor, 0 is the primary monitor.

        @throws ValueError if windowName is empty, if screens is not a list of 4-number tuples with positive width and height, or if screen is not an integer. 
        @throws IndexError if screen does not exist in screens.
        """


        self.__windowOpen = None

        self.__fullscreen = None

        self.__screen = None

        self.__screens = None

        self.__windowName = None

        self.__placedScreen = None

        # ˅
        self.__windowName = Display.__validateWindowName(windowName)
        self.__screens = Display.__validateScreens(screens)
        self.__windowOpen = False
        self.__fullscreen = False
        if self.__screens is None:
            # Placement is not configured, so there is no list to check the number against:
            # only its type is checked.
            self.__screen = Display.__validateIndexType(screen)
        else:
            self.setScreen(screen)
        # ˄

    # ˅

    @staticmethod
    def __windowMode(enabled):
        return cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL

    @staticmethod
    def __validateWindowName(windowName):
        if not isinstance(windowName, str) or not windowName.strip():
            raise ValueError(
                f"windowName must be a non-empty string, got {windowName!r}"
            )
        return windowName

    @staticmethod
    def __validateScreens(screens):
        if screens is None:
            return None
        if isinstance(screens, (str, bytes)) or not isinstance(screens, (list, tuple)):
            raise ValueError(
                "screens must be a list of (x, y, width, height) tuples "
                f"or None, got {screens!r}"
            )
        if len(screens) == 0:
            return None
        checked = []
        for entry in screens:
            if isinstance(entry, (str, bytes)) or not isinstance(entry, (list, tuple)):
                raise ValueError(
                    "each screen must be a 4-tuple of ints "
                    f"(x, y, width, height), got {entry!r}"
                )
            if len(entry) != 4:
                raise ValueError(
                    "each screen must be a 4-tuple of ints "
                    f"(x, y, width, height), got {entry!r}"
                )
            for value in entry:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(
                        "each screen must be a 4-tuple of ints "
                        f"(x, y, width, height), got {entry!r}"
                    )
            x, y, width, height = entry
            if width <= 0 or height <= 0:
                raise ValueError(
                    f"screen width and height must be greater than 0 px, got {entry!r}"
                )
            checked.append((x, y, width, height))
        return checked

    @staticmethod
    def __validateIndexType(index):
        if isinstance(index, bool) or not isinstance(index, int):
            raise ValueError(f"screen index must be an int, got {index!r}")
        return index

    def __resolveIndex(self, index):
        Display.__validateIndexType(index)
        count = len(self.__screens) if self.__screens is not None else 0
        if count == 0:
            raise IndexError(
                f"screen index {index} is out of range: 0 monitors configured "
                "(screens=None disables placement)"
            )
        if index < 0 or index >= count:
            raise IndexError(
                f"screen index {index} is out of range: {count} monitor(s) configured"
            )
        return index
    # ˄


# ˅

def screenRects(cocoaFrames):
    """!
    @package screenRects (display module function)
    @brief Converts macOS Cocoa monitor rectangles coordinates to top-left origin coordinates.
    
    @details Cocoa system uses a bottom-left origin. This function transforms it into the more common top-left origin coordinate system.
    
    @param cocoaFrames, List of monitor rectangles as (x, y, width, height). The first is the primary monitor.
    @returns screens, List of (x, y, width, height) rectangles with a top-left origin. 
    """

    primaryHeight = cocoaFrames[0][3]
    return [(int(x), int(primaryHeight - (y + height)), int(width), int(height))
            for x, y, width, height in cocoaFrames]

def findProjectorScreens():
    """!
    @package findProjectorScreens (display module function)
    @brief Detects connected monitors and selects the primary projector.
    @memberof Display

    @details The projector is the first non-primary monitor. 
    With one monitor, or if the monitors cannot be read, it uses the primary one.
    @raisewarning Works only on macOS. On other systems, returns (None, 0)

    @returns (screens, index), screens may be none.

    """

    try:
        import AppKit
        frames = [(f.origin.x, f.origin.y, f.size.width, f.size.height)
                  for f in (s.frame() for s in AppKit.NSScreen.screens())]
    except Exception:
        return None, 0
    if not frames:
        return None, 0
    rects = screenRects(frames)
    return rects, (1 if len(rects) > 1 else 0)

# ˄

#@cond
# NOTE: everything below is a manual smoke test, NOT content generated from the
# UML model. It lives outside the `# ˅` / `# ˄` markers on purpose and must stay
# at the very end of the file.
if __name__ == "__main__":
    import os

    from image import Image

    sampleDir = "images"
    samplePath = os.path.join(sampleDir, "sample.jpg")
    windowName = "PBL4 TEST"
    delayMs = 50
    # Bounded loop so an unattended run can never hang: 600 * 50 ms = 30 s max.
    maxLoops = 600

    # Target monitors as (x, y, width, height) in LOGICAL pixels, index 0 is the
    # one to show on. Fill this in for your own desk layout.
    screens = [(0, 0, 1920, 1080)]

    def buildTestImage(width=1280, height=720):
        
        upperHeight = height // 2
        lowerHeight = height - upperHeight

        bars = np.zeros((upperHeight, width, 3), dtype=np.uint8)
        colours = [
            (255, 255, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0),
            (255, 0, 255), (0, 0, 255), (255, 0, 0), (0, 0, 0),
        ]
        barWidth = width // len(colours)
        for i, colour in enumerate(colours):
            bars[:, i * barWidth:(i + 1) * barWidth] = colour

        cell = 80
        yy, xx = np.indices((lowerHeight, width))
        checker = (((yy // cell) + (xx // cell)) % 2 * 200 + 20).astype(np.uint8)
        lower = np.dstack([checker, checker, checker])

        frame = np.vstack([bars, lower])
        cv2.putText(frame, "PBL4 TEST", (40, upperHeight + lowerHeight // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, "PBL4 TEST", (40, upperHeight + lowerHeight // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "window: %s" % windowName, (40, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 3, cv2.LINE_AA)
        return frame

    testImage = buildTestImage()
    os.makedirs(sampleDir, exist_ok=True)
    if not cv2.imwrite(samplePath, testImage):
        raise RuntimeError("failed to write test image: '%s'" % samplePath)
    print("wrote %s" % samplePath)

    image = Image()
    frame = image.load(samplePath)
    print("loaded %s shape=%s" % (samplePath, image.getShape()))

    display = Display(windowName=windowName, screens=screens, screen=0)
    try:
        display.show(frame)
        display.setFullscreen(True)
        print("target screen=%s" % (screens[0],))
        print("fullscreen=%s -- press q or ESC to quit (auto-closes after %d s)"
              % (display.isFullscreen(), maxLoops * delayMs // 1000))
        for _ in range(maxLoops):
            key = display.waitKey(delayMs)
            # Mask off modifier bits: some backends return a larger code.
            if key != -1 and (key & 0xFF) in (ord("q"), 27):
                break
    finally:
        display.close()
    print("closed")
#@endcond