# Software usage {#software_usage}

Once the projectors are in place (see @ref hardware_setup "Hardware setup"),
install the program on both computers, one for each projector. It needs Python 3.14,
`numpy` and `opencv-python`. `pytest` is only for development.

## Install

We use [uv](https://docs.astral.sh/uv/) because it fetches the right Python
version by itself.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/maksym-syd/video_projector.git
cd video_projector
uv sync
```

That first line is for macOS and Linux. On Windows run
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
instead. `uv sync` creates `.venv/` and installs the versions in `uv.lock`.

If uv is not an option, make a Python 3.14 virtual environment and use pip:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate it with `.venv\Scripts\Activate.ps1`.

## Settings

`SetupClass` reads the settings from a JSON file and rejects values that do
not make sense. `settings.json` is an example for a picture and
`settings.video.json` an example for a video.

| Setting | Key | Value |
|---------|-----|-------|
| Projector resolution | `projectorResXY` | native resolution of the projectors, `[width, height]` |
| Image width | `imageWidthCm` | `w` from the hardware setup |
| Projector spacing | `projectorSpacingCm` | `d` from the hardware setup |
| Blending gamma | `blendCurveGamma` | how fast the brightness fades in the overlap |
| Source path | `sourcePath` | picture or video to project |
| Side | `projectorSide` | `LEFT` or `RIGHT` |
| Scale mode (optional) | `scaleMode` | `crop` (default) fills the combined image and cuts the edges, `fit` shows the whole picture with black bars |

The file extension of `sourcePath` decides between picture and video. Video
extensions are `.mp4`, `.m4v`, `.mov`, `.avi`, `.mkv` and `.webm`. A relative
path is taken from the folder of the settings file.

The test video that `settings.video.json` uses is not in Git. Make it with
`uv run python tools/make_test_video.py`.

## Run

Start `main.py` on each computer and give each its own side. `--side` and
`--scale-mode` override the settings file.

```bash
uv run python main.py settings.json --side LEFT
uv run python main.py settings.json --side RIGHT
```

## Video

A video shows its first frame, then starts when you press any key or at a
shared start time. It loops at the end and stops when you press `q` or `ESC`.
Video has no sound. If a file will not open, OpenCV does not support the
codec: re-encode it as H.264 `.mp4`.

To start both computers together, give both the same time. The formats are
`HH:MM`, `HH:MM:SS` and `YYYY-MM-DD HH:MM:SS`, in local time.

```bash
uv run python main.py settings.video.json --side LEFT --start-at 14:30:05
uv run python main.py settings.video.json --side RIGHT --start-at 14:30:05
```

Each frame is chosen from the clock, so the two computers' clocks must be set
right, for example with NTP. Without a start time they start only as closely
as the two key presses.

## Quick test on the projectors

`instant_run.py` shows the test video with one short command. Both laptops
need the repository and the environment installed (see Install).

On the first laptop, choose the side and a start time far enough ahead to
reach the second laptop. Without `--start-in` the video starts in 5 seconds.

```bash
uv run python instant_run.py --left --start-in 30
```

It prints the start time and the exact command for the second laptop, for
example:

```bash
uv run python instant_run.py --right --start-at '2026-11-07 14:30:35'
```

Run that command in the repository folder on the second laptop. Both videos
start by themselves at that time, with no key press. A laptop that starts
late joins at the right frame. Both laptops need the same clock and time
zone, set to automatic time.

Add `--image` to show the picture from `settings.json` instead. A picture
has no start time. Without `--left` or `--right` the command shows a preview
on this computer, and `--gui` opens the test window. If the test video is
missing, it is made first.

## Test window

`gui.py` tries settings on one computer without projectors. It previews both
sides joined, plays videos, and can start `main.py` on a projector.

```bash
uv run python gui.py settings.json
```

It needs `tkinter`. Check it with `python -c "import tkinter"`. If that fails,
run `brew install python-tk@3.14` for Homebrew Python, or
`sudo apt install python3-tk` on Debian or Ubuntu.

The Python that uv downloads itself (`--managed-python`) includes `tkinter`,
but in a virtual environment the window can still fail with
`Can't find a usable init.tcl`. The README explains how to fix this.

## Check the displays first

Before running the pipeline, make sure each projector shows up as its own
screen. `display.py` ends with a smoke test for this. It draws a test
picture, saves it as `images/sample.jpg`, loads it back and shows it
full-screen.

```bash
uv run python display.py
```

Press `q` or `ESC` to close it. It also closes on its own after 30 seconds.
To pick the screen, edit the `screens` list in the smoke test. Each entry is
`(x, y, width, height)` in logical pixels, and the picture appears on index
0.

Tests run with `uv run pytest`.

@note Most modules are generated from a UML model. Keep the `# ˅` and `# ˄`
markers and write your code between them, otherwise it is overwritten the
next time the code is generated.

Back to the @ref index "main page".
