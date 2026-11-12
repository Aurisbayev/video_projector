# Software setup and usage {#software_usage}

Install the project on both computers, one computer for each projector. Both installations should use the same project version, source file, and projection settings. The only setting that should differ is the projector side (`LEFT` or `RIGHT`).

The project requires **Python 3.14 or later**, NumPy, and OpenCV. The test suite uses `pytest`. The recommended installer is [uv](https://docs.astral.sh/uv/), which can download the Python version specified by the project and install the locked dependencies.

## 1. Install the software

Install `uv` first.

**macOS and Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Clone the repository and install its dependencies:

```bash
git clone https://github.com/maksym-syd/video_projector.git
cd video_projector
uv sync
```

`uv sync` creates a local `.venv` environment and installs the dependencies recorded in `uv.lock`. The project configuration specifies Python 3.14 or later.

### Alternative: install with pip

If you do not want to use `uv`, install Python 3.14 or later, create a virtual environment, activate it, and install the project requirements.

**macOS and Linux:**

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The commands below use `uv run`. If you installed with pip, activate `.venv` first and replace `uv run python` with `python`.

## 2. Configure the project

The program reads its configuration from a JSON file. The repository includes:

- `settings.json` — example configuration for a picture.
- `settings.video.json` — example configuration for a video.

Edit the settings on both computers so that the geometry, source path, blend setting, and scaling mode match. Set `projectorSide` to `LEFT` on the computer connected to the left projector and `RIGHT` on the other computer.

| JSON key | Purpose |
|---|---|
| `projectorResXY` | Projector's native resolution as `[width, height]` in pixels. |
| `imageWidthCm` | Width `w` covered by one projected image, in cm. |
| `projectorSpacingCm` | Distance `d` between the projectors, in cm. |
| `blendCurveGamma` | Controls the shape of the brightness fade in the overlap. |
| `sourcePath` | Path to the picture or video to display. |
| `projectorSide` | `LEFT` or `RIGHT`, identifying this computer's projector. |
| `scaleMode` | Optional. `crop` fills the combined image and cuts off excess edges; `fit` shows the whole source with black bars. Defaults to `crop`. |

A relative `sourcePath` is resolved from the directory containing the settings file. Both computers must be able to read the source at the configured path.

Supported video extensions are `.mp4`, `.m4v`, `.mov`, `.avi`, `.mkv`, and `.webm`. Actual playback also depends on the codec being supported by the installed OpenCV build. Video playback has no audio.

The example video settings refer to `test_images/demo.mp4`, which is generated locally and is not included in the repository. From the repository root, create it with:

```bash
uv run python tools/make_test_video.py
```

## 3. Run the projection program

Run `main.py` on each computer, using the same settings file and the appropriate side:

```bash
uv run python main.py settings.json --side LEFT
uv run python main.py settings.json --side RIGHT
```

The `--side` option overrides `projectorSide` in the JSON file. The optional `--scale-mode crop` or `--scale-mode fit` option overrides `scaleMode`.

For a video, the first frame is displayed before playback starts. Press any key to start, then press `q` or `Esc` to stop. The video loops when it reaches the end.

### Synchronize video playback

To schedule both computers to start at the same time, pass the same local time to each process using `--start-at`:

```bash
uv run python main.py settings.video.json --side LEFT --start-at 14:30:05
uv run python main.py settings.video.json --side RIGHT --start-at 14:30:05
```

Accepted time formats are `HH:MM`, `HH:MM:SS`, `YYYY-MM-DD HH:MM`, and `YYYY-MM-DD HH:MM:SS`. Use local time and give both computers the same time and time zone.

Each computer chooses the frame corresponding to the clock time. A computer that starts late can join at the appropriate frame rather than beginning from the first frame. For this to work, keep both computer clocks synchronized, for example by enabling automatic time synchronization. Without `--start-at`, the computers begin after separate key presses, so a small timing difference is expected.

`--start-at` is ignored for a picture source.

## 4. Quick test with `instant_run.py`

`instant_run.py` is a launcher for the test video or picture. Run it from the repository root on both computers.

On the first computer, start the left projector and schedule the video to begin in 30 seconds:

```bash
uv run python instant_run.py --left --start-in 30
```

The command prints the start time and a command for the second computer. Run the printed command on the second computer from its repository folder. The second computer should use the opposite side. Both computers need synchronized clocks and the same time zone.

Useful options:

- `--left` or `--right` — run the real projection program for that side.
- `--video` — use `settings.video.json` (the default).
- `--image` — use `settings.json`; a picture does not use a start time.
- `--start-in SECONDS` — schedule a start a number of seconds in the future.
- `--start-at TIME` — use an explicitly specified shared local time.
- No side option — open a joined preview on the current computer.
- `--gui` — open the test GUI. It cannot be combined with a side or start-time option.

Examples:

```bash
uv run python instant_run.py --left
uv run python instant_run.py --right
uv run python instant_run.py --image
uv run python instant_run.py --gui
```

The default video start delay is five seconds when a side is selected and no start option is supplied.

## 5. Use the test GUI

The GUI lets you try settings and preview the combined output on one computer without connecting projectors:

```bash
uv run python gui.py settings.json
```

It can edit settings, show the joined left and right output, preview pictures and videos, compare blending on and off, and start the projection program.

The GUI requires `tkinter`. Check whether the active Python can import it:

```bash
python -c "import tkinter"
```

If `tkinter` is missing, install the matching package for your Python distribution. For example:

**Homebrew Python:**

```bash
brew install python-tk@3.14
```

**Debian or Ubuntu:**

```bash
sudo apt install python3-tk
```

The Python managed by `uv` normally includes `tkinter`, but a GUI can still fail if its Tcl/Tk files cannot be found. See the repository README for additional troubleshooting.

## 6. Check the connected displays

Before running the projection pipeline, confirm that the operating system detects each projector as a separate display. The `display.py` smoke test opens a test image on a selected display:

```bash
uv run python display.py
```

Press `q` or `Esc` to close the test. It also closes automatically after 30 seconds. The display rectangles are configured in the smoke-test section of `display.py`; each rectangle is `(x, y, width, height)` in logical pixels.

## 7. Run the tests

Install the development dependencies and run the test suite:

```bash
uv sync --group dev
uv run pytest
```

The tests check the geometry calculations, settings validation, image processing, video handling, display behaviour, and pipeline components.

@note Some modules are generated from a UML model. Keep the `# ˅` and `# ˄` markers and make changes only in the designated code sections; edits outside those markers may be overwritten when the code is generated.

Back to the @ref mainpage "main page".
