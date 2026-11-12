#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@package gui Provides a graphical interface for configuring and previewing the system.

Test GUI: edit the settings, see both projectors joined (picture or video), start the real show.

python gui.py [settings.json]

PreviewEngine does the work and has no window code, so it can be tested without a screen.
App is the tkinter window around it.
"""
import json
import logging
import os
import subprocess
import sys
import tempfile
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from image import Image
from math_class import MathClass
from pipeline_class import PipelineClass
from setup_class import SetupClass
from side import Side
from tools.preview_both import join
from video_source import VideoSource, parseStartTime

GAMMA_MIN, GAMMA_MAX = 0.5, 3.0
DEFAULT_SETTINGS = {
    "projectorResXY": [1920, 1080],
    "imageWidthCm": 134.0,
    "projectorSpacingCm": 108.0,
    "blendCurveGamma": 2.0,
    "sourcePath": "",
    "projectorSide": "LEFT",
    "scaleMode": "crop",
}
VIEWS = ("both", "left", "right")
GUIDE_COLOR = (255, 200, 0)  # BGR
SCALE_MODES = ("crop", "fit")


class _Messages(logging.Handler):
    """Collects the reason SetupClass.validate() logs when it says no."""

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


class PreviewEngine(object):
    """Holds the settings and the LEFT and RIGHT pipelines, and draws the joined preview."""

    def apply(self, settings):
        """Use these settings (a dict like settings.json). Returns a list of problems, empty if fine."""
        self.__ready = False
        settings = dict(settings)
        if isinstance(settings.get("sourcePath"), str) and settings["sourcePath"].strip():
            # The pipelines read temporary settings files, so a relative path would be
            # looked up in the wrong folder.
            settings["sourcePath"] = os.path.abspath(os.path.expanduser(settings["sourcePath"].strip()))
        try:
            probe = self.__buildPipelines(settings)
        except (OSError, ValueError) as e:
            return [str(e)]
        self.__pipes = probe
        self.__settings = dict(settings)
        problem = self.__openSource(settings["sourcePath"])
        if problem:
            return [problem]
        self.__ready = True
        return []

    def isReady(self):
        return self.__ready

    def isVideo(self):
        return self.__ready and self.__video is not None

    def getFps(self):
        return self.__video.getFps() if self.isVideo() else 0.0

    def getFrameCount(self):
        return self.__video.getFrameCount() if self.isVideo() else 1

    def getLayout(self):
        """Return (overlapCm, overlapPx, combinedWidthPx) for the current settings."""
        resX = self.__settings["projectorResXY"][0]
        w = self.__settings["imageWidthCm"]
        d = self.__settings["projectorSpacingCm"]
        overlapPx = MathClass.overlapPx(resX, w, d)
        return MathClass.overlapCm(w, d), overlapPx, 2 * resX - overlapPx

    def render(self, index=0, view="both", blend=True, guide=False, projectorGamma=None):
        """Return the preview picture (BGR) for frame number index.

        view: "both" (joined), "left" or "right" (what that projector shows)
        blend: False leaves the mask out, so the overlap is not faded
        guide: True draws lines at the edges of the overlap
        projectorGamma: None adds pixel values; a number (about 2.2) adds light like the wall does
        """
        if not self.__ready:
            raise ValueError("The settings are not usable yet")
        if view not in VIEWS:
            raise ValueError("view must be one of %s, got %r" % (VIEWS, view))
        raw = self.__video.frameAt(index % self.__video.getFrameCount()) if self.isVideo() else self.__still
        _, overlapPx, _ = self.getLayout()
        left = self.__pipes[Side.LEFT].processFrame(raw, masked=blend).getFrame()
        right = self.__pipes[Side.RIGHT].processFrame(raw, masked=blend).getFrame()
        resX = left.shape[1]
        if view == "left":
            picture, marks = left, (resX - overlapPx, resX)
        elif view == "right":
            picture, marks = right, (0, overlapPx)
        else:
            picture, marks = join(left, right, overlapPx, projectorGamma), (resX - overlapPx, resX)
        picture = np.ascontiguousarray(picture)
        if guide and overlapPx > 0:
            for x in marks:
                x = min(max(x, 0), picture.shape[1] - 1)
                cv2.line(picture, (x, 0), (x, picture.shape[0] - 1), GUIDE_COLOR, 2)
        return picture

    def close(self):
        if self.__video is not None:
            self.__video.close()
            self.__video = None
        self.__ready = False

    def __buildPipelines(self, settings):
        pipes = {}
        handler = _Messages()
        log = logging.getLogger("setup_class")
        log.addHandler(handler)
        try:
            for side in (Side.LEFT, Side.RIGHT):
                path = os.path.join(self.__folder, "%s.json" % side.name.lower())
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(dict(settings, projectorSide=side.name), f)
                setup = SetupClass()
                setup.load(path)
                if not setup.validate():
                    raise ValueError(handler.messages[-1] if handler.messages else "Invalid settings")
                pipes[side] = PipelineClass(setup)
        finally:
            log.removeHandler(handler)
        return pipes

    def __openSource(self, path):
        """Open the picture or video. Returns a problem text, or None if it worked."""
        if self.__video is not None:
            self.__video.close()
            self.__video = None
        self.__still = None
        try:
            if VideoSource.isVideoPath(path):
                self.__video = VideoSource(path)
            else:
                self.__still = Image().load(path)
        except (OSError, ValueError) as e:
            return str(e)
        return None

    def __init__(self):
        self.__folder = tempfile.mkdtemp(prefix="projector_gui_")
        self.__settings = None
        self.__pipes = {}
        self.__video = None
        self.__still = None
        self.__ready = False


def loadSettings(path):
    """Read a settings file into a plain dict, with the defaults for anything missing."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Settings file '%s' must contain a JSON object" % path)
    settings = dict(DEFAULT_SETTINGS)
    settings.update({k: data[k] for k in DEFAULT_SETTINGS if k in data})
    source = settings["sourcePath"]
    if isinstance(source, str) and source.strip():
        # Same rule as SetupClass.load(): a relative path is relative to the settings file.
        source = os.path.expanduser(source.strip())
        if not os.path.isabs(source):
            source = os.path.join(os.path.dirname(os.path.abspath(path)), source)
        settings["sourcePath"] = source
    return settings


def buildStartCommand(settingsFile, side, startAt=None):
    """The command that starts the real show on this computer's projector.

    startAt: text like 14:30:05 for a shared start time, or empty/None for a key press start.
    Raises ValueError if startAt is not a time.
    """
    command = [sys.executable, os.path.join(ROOT, "main.py"), settingsFile, "--side", side]
    if startAt is not None and str(startAt).strip():
        parseStartTime(str(startAt))
        command += ["--start-at", str(startAt).strip()]
    return command


def relativeTo(path, folder):
    """path written relative to folder when that is possible, so saved settings can be moved."""
    try:
        return os.path.relpath(path, folder)
    except ValueError:
        return path


def toPhoto(tk, bgr):
    """Make a tkinter image from a BGR picture, without needing PIL."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    height, width = rgb.shape[:2]
    return tk.PhotoImage(data=b"P6 %d %d 255\n" % (width, height) + rgb.tobytes(), format="PPM")


def fitInto(picture, width, height):
    """Shrink or enlarge a picture to fit a box, keeping the proportions."""
    h, w = picture.shape[:2]
    scale = min(max(width, 1) / w, max(height, 1) / h)
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return cv2.resize(picture, size, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)


def runApp(argv=None):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class App(tk.Tk):

        def __init__(self, settings, settingsPath=None):
            super().__init__()
            self.title("Dual Projector: test GUI")
            self.geometry("1280x760")
            self.minsize(900, 560)
            self.__engine = PreviewEngine()
            self.__settingsPath = settingsPath
            self.__process = None
            self.__pending = None
            self.__tick = None
            self.__updating = False
            self.__playing = True
            self.__startTime = time.monotonic()
            self.__pausedAt = 0.0
            self.__lastKey = None
            self.__photo = None

            self.__source = tk.StringVar(value=settings["sourcePath"])
            self.__resX = tk.StringVar(value=str(settings["projectorResXY"][0]))
            self.__resY = tk.StringVar(value=str(settings["projectorResXY"][1]))
            self.__w = tk.StringVar(value=str(settings["imageWidthCm"]))
            self.__d = tk.StringVar(value=str(settings["projectorSpacingCm"]))
            self.__gamma = tk.DoubleVar(value=float(settings["blendCurveGamma"]))
            self.__side = tk.StringVar(value=str(settings["projectorSide"]).upper())
            self.__scale = tk.StringVar(value=str(settings.get("scaleMode", "crop")).lower())
            self.__startAt = tk.StringVar()
            self.__view = tk.StringVar(value="both")
            self.__blend = tk.BooleanVar(value=True)
            self.__guide = tk.BooleanVar(value=False)
            self.__simulate = tk.BooleanVar(value=True)
            self.__projGamma = tk.StringVar(value="2.2")
            self.__info = tk.StringVar()
            self.__status = tk.StringVar()
            self.__build()
            for var in (self.__source, self.__resX, self.__resY, self.__w, self.__d, self.__gamma, self.__scale):
                var.trace_add("write", lambda *_: self.__scheduleApply())
            for var in (self.__view, self.__blend, self.__guide, self.__simulate, self.__projGamma):
                var.trace_add("write", lambda *_: self.__redraw())
            self.protocol("WM_DELETE_WINDOW", self.__quit)
            self.bind("<space>", lambda e: self.__togglePlay() if e.widget.winfo_class() not in ("TEntry", "TSpinbox") else None)
            self.__apply()
            self.__loop()

        # ---- layout ----
        def __build(self):
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            side = ttk.Frame(self, padding=10)
            side.grid(row=0, column=0, sticky="ns")
            ttk.Label(side, text="Settings", font=("", 13, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")

            ttk.Label(side, text="Picture or video").grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
            ttk.Entry(side, textvariable=self.__source, width=30).grid(row=2, column=0, columnspan=2, sticky="we")
            ttk.Button(side, text="Browse…", command=self.__browse).grid(row=2, column=2, padx=(4, 0))

            ttk.Label(side, text="Projector resolution [px]").grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
            res = ttk.Frame(side)
            res.grid(row=4, column=0, columnspan=3, sticky="w")
            ttk.Spinbox(res, from_=320, to=7680, increment=10, textvariable=self.__resX, width=7).pack(side="left")
            ttk.Label(res, text=" x ").pack(side="left")
            ttk.Spinbox(res, from_=240, to=4320, increment=10, textvariable=self.__resY, width=7).pack(side="left")

            ttk.Label(side, text="w: width of one projector's picture [cm]").grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))
            ttk.Spinbox(side, from_=10, to=2000, increment=1, textvariable=self.__w, width=9).grid(row=6, column=0, sticky="w")
            ttk.Label(side, text="d: distance between projectors [cm]").grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 0))
            ttk.Spinbox(side, from_=1, to=2000, increment=1, textvariable=self.__d, width=9).grid(row=8, column=0, sticky="w")

            ttk.Label(side, text="Gamma (fade shape)").grid(row=9, column=0, columnspan=3, sticky="w", pady=(8, 0))
            ttk.Scale(side, from_=GAMMA_MIN, to=GAMMA_MAX, variable=self.__gamma, length=230).grid(row=10, column=0, columnspan=2, sticky="we")
            self.__gammaText = ttk.Label(side, width=5)
            self.__gammaText.grid(row=10, column=2)

            scale = ttk.Frame(side)
            scale.grid(row=11, column=0, columnspan=3, sticky="w", pady=(8, 0))
            ttk.Label(scale, text="Fit picture: ").pack(side="left")
            ttk.Combobox(scale, textvariable=self.__scale, values=SCALE_MODES, width=6, state="readonly").pack(side="left")
            ttk.Label(scale, text=" crop fills, fit shows it all", foreground="#444").pack(side="left")

            ttk.Label(side, textvariable=self.__info, justify="left", foreground="#444").grid(row=12, column=0, columnspan=3, sticky="w", pady=(10, 0))

            ttk.Separator(side).grid(row=13, column=0, columnspan=3, sticky="we", pady=10)
            ttk.Label(side, text="Preview", font=("", 13, "bold")).grid(row=14, column=0, sticky="w")
            views = ttk.Frame(side)
            views.grid(row=15, column=0, columnspan=3, sticky="w")
            for text, value in (("Both joined", "both"), ("LEFT only", "left"), ("RIGHT only", "right")):
                ttk.Radiobutton(views, text=text, value=value, variable=self.__view).pack(side="left", padx=(0, 6))
            ttk.Checkbutton(side, text="Blend on (off shows the overlap unfaded)", variable=self.__blend).grid(row=16, column=0, columnspan=3, sticky="w")
            ttk.Checkbutton(side, text="Show overlap edges", variable=self.__guide).grid(row=17, column=0, columnspan=3, sticky="w")

            sim = ttk.Frame(side)
            sim.grid(row=18, column=0, columnspan=3, sticky="w")
            ttk.Checkbutton(sim, text="Like the wall: add light, projector gamma", variable=self.__simulate).pack(side="left")
            ttk.Spinbox(sim, from_=1.0, to=3.0, increment=0.1, textvariable=self.__projGamma, width=4).pack(side="left", padx=4)

            files = ttk.Frame(side)
            files.grid(row=19, column=0, columnspan=3, sticky="w", pady=(10, 0))
            ttk.Button(files, text="Open settings…", command=self.__openSettings).pack(side="left")
            ttk.Button(files, text="Save settings…", command=self.__saveSettings).pack(side="left", padx=4)
            ttk.Button(side, text="Save this picture…", command=self.__savePicture).grid(row=20, column=0, columnspan=3, sticky="w", pady=(4, 0))

            ttk.Separator(side).grid(row=21, column=0, columnspan=3, sticky="we", pady=10)
            ttk.Label(side, text="On this computer's projector", font=("", 13, "bold")).grid(row=22, column=0, columnspan=3, sticky="w")
            sides = ttk.Frame(side)
            sides.grid(row=23, column=0, columnspan=3, sticky="w")
            ttk.Label(sides, text="This computer drives: ").pack(side="left")
            for value in ("LEFT", "RIGHT"):
                ttk.Radiobutton(sides, text=value, value=value, variable=self.__side).pack(side="left", padx=2)
            at = ttk.Frame(side)
            at.grid(row=24, column=0, columnspan=3, sticky="w", pady=(4, 0))
            ttk.Label(at, text="Video start at (HH:MM:SS): ").pack(side="left")
            ttk.Entry(at, textvariable=self.__startAt, width=9).pack(side="left")
            ttk.Button(at, text="In 15 s", width=7, command=lambda: self.__startIn(15)).pack(side="left", padx=2)
            ttk.Button(at, text="In 30 s", width=7, command=lambda: self.__startIn(30)).pack(side="left")
            ttk.Label(side, text="Same time on both computers. Empty: a key press starts the video.",
                      foreground="#444").grid(row=25, column=0, columnspan=3, sticky="w")
            runs = ttk.Frame(side)
            runs.grid(row=26, column=0, columnspan=3, sticky="w", pady=(4, 0))
            ttk.Button(runs, text="Start on projector", command=self.__start).pack(side="left")
            ttk.Button(runs, text="Stop", command=self.__stop).pack(side="left", padx=4)

            main = ttk.Frame(self, padding=(0, 10, 10, 0))
            main.grid(row=0, column=1, sticky="nsew")
            main.columnconfigure(0, weight=1)
            main.rowconfigure(0, weight=1)
            self.__canvas = tk.Label(main, background="#111", anchor="center")
            self.__canvas.grid(row=0, column=0, sticky="nsew")
            bar = ttk.Frame(main)
            bar.grid(row=1, column=0, sticky="we", pady=6)
            bar.columnconfigure(1, weight=1)
            self.__playButton = ttk.Button(bar, text="Pause", width=8, command=self.__togglePlay)
            self.__playButton.grid(row=0, column=0)
            self.__position = ttk.Scale(bar, from_=0, to=1, command=self.__seek)
            self.__position.grid(row=0, column=1, sticky="we", padx=8)
            self.__timeText = ttk.Label(bar, width=14, anchor="e")
            self.__timeText.grid(row=0, column=2)
            ttk.Label(self, textvariable=self.__status, anchor="w", padding=(10, 2)).grid(row=1, column=0, columnspan=2, sticky="we")

        # ---- settings ----
        def __current(self):
            """The settings from the fields, or raises ValueError naming the wrong field."""
            def number(var, name, kind):
                try:
                    return kind(var.get())
                except (ValueError, tk.TclError):
                    raise ValueError("%s must be a number" % name)
            return {
                "projectorResXY": [number(self.__resX, "Resolution width", int), number(self.__resY, "Resolution height", int)],
                "imageWidthCm": number(self.__w, "w", float),
                "projectorSpacingCm": number(self.__d, "d", float),
                "blendCurveGamma": round(number(self.__gamma, "Gamma", float), 2),
                "sourcePath": self.__source.get().strip(),
                "projectorSide": self.__side.get(),
                "scaleMode": self.__scale.get(),
            }

        def __scheduleApply(self):
            self.__gammaText.configure(text="%.2f" % self.__gamma.get())
            if self.__pending is not None:
                self.after_cancel(self.__pending)
            self.__pending = self.after(250, self.__apply)

        def __apply(self):
            self.__pending = None
            try:
                settings = self.__current()
            except ValueError as e:
                self.__fail(str(e))
                return
            problems = self.__engine.apply(settings)
            self.__gammaText.configure(text="%.2f" % settings["blendCurveGamma"])
            if problems:
                self.__fail(problems[0])
                return
            overlapCm, overlapPx, width = self.__engine.getLayout()
            self.__info.set("Overlap: %.1f cm = %d px\nCombined picture: %d x %d px"
                            % (overlapCm, overlapPx, width, settings["projectorResXY"][1]))
            self.__status.set("Video, %d frames at %.1f fps" % (self.__engine.getFrameCount(), self.__engine.getFps())
                              if self.__engine.isVideo() else "Picture")
            self.__position.configure(to=max(1, self.__engine.getFrameCount() - 1))
            self.__startTime = time.monotonic()
            self.__pausedAt = 0.0
            self.__lastKey = None

        def __fail(self, text):
            self.__info.set("")
            self.__status.set("Problem: " + text)
            self.__lastKey = None

        def __browse(self):
            path = filedialog.askopenfilename(title="Choose a picture or video", initialdir=ROOT, filetypes=[
                ("Pictures and videos", "*.jpg *.jpeg *.png *.bmp *.mp4 *.m4v *.mov *.avi *.mkv *.webm"), ("All files", "*.*")])
            if path:
                self.__source.set(path)

        def __openSettings(self):
            path = filedialog.askopenfilename(title="Open settings", initialdir=ROOT, filetypes=[("JSON", "*.json")])
            if not path:
                return
            try:
                s = loadSettings(path)
            except (OSError, ValueError) as e:
                messagebox.showerror("Cannot open settings", str(e))
                return
            self.__settingsPath = path
            self.__source.set(s["sourcePath"])
            self.__resX.set(str(s["projectorResXY"][0]))
            self.__resY.set(str(s["projectorResXY"][1]))
            self.__w.set(str(s["imageWidthCm"]))
            self.__d.set(str(s["projectorSpacingCm"]))
            self.__gamma.set(float(s["blendCurveGamma"]))
            self.__side.set(str(s["projectorSide"]).upper())
            self.__scale.set(str(s["scaleMode"]).lower())

        def __saveSettings(self):
            try:
                settings = self.__current()
            except ValueError as e:
                messagebox.showerror("Cannot save", str(e))
                return
            path = filedialog.asksaveasfilename(title="Save settings", initialdir=ROOT, defaultextension=".json",
                                                initialfile=os.path.basename(self.__settingsPath or "settings.json"))
            if path:
                if settings["sourcePath"]:
                    settings["sourcePath"] = relativeTo(os.path.abspath(settings["sourcePath"]), os.path.dirname(os.path.abspath(path)))
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2)
                self.__settingsPath = path
                self.__status.set("Saved " + path)

        def __savePicture(self):
            if not self.__engine.isReady():
                return
            path = filedialog.asksaveasfilename(title="Save picture", defaultextension=".png", initialfile="preview.png")
            if path:
                picture = self.__engine.render(self.__frameIndex(), self.__view.get(), self.__blend.get(), self.__guide.get(), self.__lightGamma())
                cv2.imwrite(path, picture)
                self.__status.set("Saved " + path)

        # ---- the real show ----
        def __start(self):
            if self.__process is not None and self.__process.poll() is None:
                self.__status.set("Already running. Press Stop first.")
                return
            try:
                settings = self.__current()
            except ValueError as e:
                messagebox.showerror("Cannot start", str(e))
                return
            if not self.__engine.isReady():
                messagebox.showerror("Cannot start", self.__status.get())
                return
            settings["sourcePath"] = os.path.abspath(settings["sourcePath"])
            path = os.path.join(tempfile.mkdtemp(prefix="projector_gui_run_"), "settings.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f)
            try:
                command = buildStartCommand(path, settings["projectorSide"], self.__startAt.get())
            except ValueError as e:
                messagebox.showerror("Cannot start", str(e))
                return
            self.__process = subprocess.Popen(command, cwd=ROOT)
            if "--start-at" in command:
                self.__status.set("Started %s. The video begins at %s; q or Esc closes it." % (settings["projectorSide"], self.__startAt.get().strip()))
            else:
                self.__status.set("Started %s on the projector. Press a key in its window to begin a video; q or Esc closes it." % settings["projectorSide"])

        def __startIn(self, seconds):
            self.__startAt.set(time.strftime("%H:%M:%S", time.localtime(time.time() + seconds)))

        def __stop(self):
            if self.__process is not None and self.__process.poll() is None:
                self.__process.terminate()
                self.__status.set("Stopped")
            self.__process = None

        # ---- playback ----
        def __frameIndex(self):
            if not self.__engine.isVideo():
                return 0
            seconds = (time.monotonic() - self.__startTime) if self.__playing else self.__pausedAt
            return int(seconds * self.__engine.getFps()) % self.__engine.getFrameCount()

        def __togglePlay(self):
            if not self.__engine.isVideo():
                return
            if self.__playing:
                self.__pausedAt = time.monotonic() - self.__startTime
            else:
                self.__startTime = time.monotonic() - self.__pausedAt
            self.__playing = not self.__playing
            self.__playButton.configure(text="Pause" if self.__playing else "Play")

        def __seek(self, value):
            if self.__updating or not self.__engine.isVideo():
                return
            seconds = float(value) / self.__engine.getFps()
            self.__pausedAt = seconds
            self.__startTime = time.monotonic() - seconds
            self.__lastKey = None

        def __lightGamma(self):
            """The projector gamma to simulate, or None if the box is off or the number is not usable."""
            if not self.__simulate.get():
                return None
            try:
                value = float(self.__projGamma.get())
            except (ValueError, tk.TclError):
                return None
            return value if value > 0 else None

        def __redraw(self):
            self.__lastKey = None

        def __loop(self):
            started = time.monotonic()
            try:
                self.__drawOnce()
            except (ValueError, OSError) as e:
                self.__fail(str(e))
            delay = max(1, 33 - int((time.monotonic() - started) * 1000))
            self.__tick = self.after(delay, self.__loop)

        def __drawOnce(self):
            if not self.__engine.isReady():
                return
            index = self.__frameIndex()
            key = (index, self.__view.get(), self.__blend.get(), self.__guide.get(), self.__lightGamma(),
                   self.__canvas.winfo_width(), self.__canvas.winfo_height())
            if key == self.__lastKey:
                return
            self.__lastKey = key
            picture = self.__engine.render(index, self.__view.get(), self.__blend.get(), self.__guide.get(), self.__lightGamma())
            self.__photo = toPhoto(tk, fitInto(picture, self.__canvas.winfo_width(), self.__canvas.winfo_height()))
            self.__canvas.configure(image=self.__photo)
            if self.__engine.isVideo():
                fps = self.__engine.getFps()
                self.__updating = True
                self.__position.set(index)
                self.__updating = False
                self.__timeText.configure(text="%.1f / %.1f s" % (index / fps, self.__engine.getFrameCount() / fps))
            else:
                self.__timeText.configure(text="")

        def __quit(self):
            self.__stop()
            if self.__tick is not None:
                self.after_cancel(self.__tick)
            self.__engine.close()
            self.destroy()

    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else (os.path.join(ROOT, "settings.json") if os.path.isfile(os.path.join(ROOT, "settings.json")) else None)
    try:
        settings = loadSettings(path) if path else dict(DEFAULT_SETTINGS)
    except (OSError, ValueError) as e:
        print("Cannot open settings: %s" % e, file=sys.stderr)
        return 1
    App(settings, path).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(runApp())
