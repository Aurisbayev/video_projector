#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ˅
import cv2
import numpy as np
# ˄


class Display(object):
    # ˅
    
    # ˄

    def setScreen(self, index):
        # ˅
        """!
        @brief Select the target monitor by index and remember that number.
        @param index index into screens (0 is the primary monitor) [none].
        @return None
        @rtype None
        @throws IndexError If screens is not configured or the index is out of range.
        """
        self.__screen = self.__resolveIndex(index)
        # ˄

    def setFullscreen(self, enabled=True):
        # ˅
        """!
        @brief Set the desired fullscreen state and apply it immediately if a window exists.
        @param enabled True for fullscreen, False for a normal window [none].
        @return None
        @rtype None
        @throws RuntimeError If called before the window is created.
        """
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
        # ˅
        """!
        @brief Return the desired fullscreen state.
        @return True if fullscreen is enabled, False otherwise [none].
        @rtype bool
        """
        return self.__fullscreen
        # ˄

    @staticmethod
    def buildTestImage(width=1280, height=720):
        # ˅
        """!
        @brief Build a test frame (BGR) with colour bars, a checker pattern and text.
        @param width frame width [px].
        @param height frame height [px].
        @return A numpy.ndarray of shape (height, width, 3) and dtype uint8 [none].
        @rtype numpy.ndarray
        """
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
        # ˅
        """!
        @brief Show a frame in the window.
        
        The first call creates the window. If screens is configured, move and resize the window to the selected monitor.
        
        @param frame image to display (numpy.ndarray) [none].
        @return None
        @rtype None
        @throws ValueError If frame is not a numpy.ndarray.
        """
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
        # ˅
        """!
        @brief Wait delayMs milliseconds for a key press and return the key code (-1 if none).
        @param delayMs wait time [ms]. 0 waits indefinitely.
        @return The key code [none].
        @rtype int
        """
        return cv2.waitKey(delayMs)
        # ˄

    def close(self):
        # ˅
        """!
        @brief Destroy the window.
        
        Does nothing if there is no window or on calls after the first.
        
        @return None
        @rtype None
        """
        if not self.__windowOpen:
            return
        cv2.destroyWindow(self.__windowName)
        self.__windowOpen = False
        # ˄

    def __init__(self, windowName="projector", screens=None, screen=0):

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
            # Placement is not configured, so keep the number without validating it.
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
    @brief Convert macOS screen frames to (x, y, width, height) with the origin at the top left.
    @param cocoaFrames [(x, y, width, height), ...] in macOS coordinates (origin at the bottom left of the primary screen) [none]. The first entry is the primary screen.
    @return A list of converted screen frames [none].
    @rtype list
    """
    primaryHeight = cocoaFrames[0][3]
    return [(int(x), int(primaryHeight - (y + height)), int(width), int(height))
            for x, y, width, height in cocoaFrames]


def findProjectorScreens():
    """!
    @brief Return the connected screens and the one to use for the projector.
    
    The projector is the first screen that is not the primary one. With a single screen, or if the screens cannot be read, the primary screen (index 0) is used and screens may be None, which leaves the window placement to the system.
    
    @return A tuple of (screens, index) [none].
    @rtype tuple
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
        """!
        @brief Build a test frame (BGR) with text overlaid on colour bars and a checker pattern.
        @param width frame width [px].
        @param height frame height [px].
        @return A numpy.ndarray of shape (height, width, 3) and dtype uint8 [none].
        @rtype numpy.ndarray
        """
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
