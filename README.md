# video_projector

Dual-projector blending with **video support**, a test GUI, a crop/fit picture mode and a shared
start time. It is the video version of the PBL4 dual-projector project (`projector_pbl4`), kept
in its own repository. Pictures and the test video are not in Git: make the test video with
`python tools/make_test_video.py`, and put your own pictures wherever `sourcePath` points.

A pipeline for multi-projector edge blending: it crops a source image for each projector (left / right), applies a blend mask to the overlapping region, and displays the result.

## Requirements

- Python **3.14** (pinned in `.python-version`)
- Dependencies (defined in `pyproject.toml`, locked in `uv.lock`)
  - Runtime: `numpy`, `opencv-python`
  - Development: `pytest`

---

## Option A: Using uv (recommended)

[uv](https://docs.astral.sh/uv/) manages the Python version, the virtual environment, and dependencies in one tool.

### 1. Install uv

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternatives**

```bash
brew install uv      # Homebrew
pipx install uv      # pipx
pip install uv       # pip
```

Restart your terminal, then check the installation:

```bash
uv --version
```

See the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/) for more options.

### 2. Set up the project

```bash
git clone https://github.com/maksym-syd/video_projector.git
cd video_projector
uv sync
```

`uv sync` downloads Python 3.14 if needed, creates `.venv/`, and installs the exact versions from `uv.lock`.

### 3. Run the code

```bash
uv run python <script>.py
uv run pytest
```

`uv run` always uses the project's virtual environment, so you don't need to activate it.

### Managing dependencies

| Task | Command |
|---|---|
| Add a runtime dependency | `uv add <package>` |
| Add a development dependency | `uv add --dev <package>` |
| Remove a dependency | `uv remove <package>` |
| Upgrade locked versions | `uv lock --upgrade` |
| Sync after pulling changes | `uv sync` |

> [!IMPORTANT]
> After you change dependencies, regenerate the requirements files (see [Option B](#option-b-without-uv-pip--venv)) and commit `pyproject.toml`, `uv.lock`, `requirements.txt`, and `requirements-dev.txt` together.

---

## Option B: Without uv (pip + venv)

If you can't install uv, you can use the standard `venv` and `pip` tools.

### 1. Install Python 3.14

Download it from [python.org](https://www.python.org/downloads/) and check the version:

```bash
python3 --version   # Windows: py -3.14 --version
```

### 2. Create and activate a virtual environment

**macOS / Linux**

```bash
git clone https://github.com/maksym-syd/video_projector.git
cd video_projector
python3.14 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/maksym-syd/video_projector.git
cd video_projector
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

The requirements files are exported from `uv.lock`, so pip installs the same versions as uv:

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt   # runtime + development (pytest)
# or, runtime only:
pip install -r requirements.txt
```

### 4. Run the code

With the virtual environment activated:

```bash
python <script>.py
pytest
```

Run `deactivate` to leave the virtual environment.

> [!NOTE]
> `requirements.txt` and `requirements-dev.txt` are generated files. Don't edit them by hand. After you change dependencies with uv, regenerate them:
>
> ```bash
> uv export --no-hashes --no-dev --format requirements-txt -o requirements.txt
> uv export --no-hashes --format requirements-txt -o requirements-dev.txt
> ```

---

## Project structure

| File | Description |
|---|---|
| `pipeline_class.py` | Main pipeline: load → scale → crop → apply mask → display |
| `setup_class.py` | Loads and validates the configuration (resolution, image width, projector spacing, gamma, source path, side) |
| `math_class.py` | Calculations for overlap, pixels per cm, crop region, and blend mask |
| `region.py` | Crop region (x start and width in pixels) |
| `mask.py` | Blend mask (alpha values) |
| `side.py` | `Side` enum (`LEFT` / `RIGHT`) |
| `image.py`, `display.py` | Image and display classes |
| `gui.py` | Test window: settings, joined preview, start on the projector |
| `video_source.py` | Reads video files frame by frame (`VideoSource`) |

> [!NOTE]
> The modules are generated from a UML model. Keep the `# ˅` / `# ˄` markers and write your code between them so it is kept when the code is regenerated.

## Pictures and videos

`sourcePath` can point at a picture (`.jpg`, `.png`, ...) or at a video
(`.mp4`, `.m4v`, `.mov`, `.avi`, `.mkv`, `.webm`). The file extension decides which.

For a video, each computer:

1. shows the first frame of its own side;
2. starts playing either when you press any key, or at a **shared start time** (see below);
3. picks each frame from the clock, not by counting, so a slow computer skips frames and
   does not fall behind the other one;
4. loops when the video ends;
5. stops when you press `q` or `ESC`.

### Shared start time

```bash
python main.py settings.json --side LEFT  --start-at 14:30:05
python main.py settings.json --side RIGHT --start-at 14:30:05
```

Give the same time (local time, `HH:MM`, `HH:MM:SS` or `YYYY-MM-DD HH:MM:SS`) on both computers.
They wait on the first frame and start together, with no key press. A computer that starts
after that time joins at the frame that belongs to that moment, so both still match. The
two computers' clocks must be set right (use automatic time, for example NTP); how close
they stay depends on how close the clocks are. In the GUI, the field "Video start at" does
the same, and "In 15 s" / "In 30 s" fill in a time a little ahead of now.

### Picture proportions

`scaleMode` in the settings (or `--scale-mode` on the command line):

- `crop` (default): the picture fills the whole combined image and the extra edges are cut off.
- `fit`: the whole picture is shown, with black bars where its proportions do not match.

Without a start time the two computers start together only as well as the two key presses.
Expect a small offset (a tenth of a second or so). Video has no sound. If a file will not open, the codec is not
supported by OpenCV: re-encode it as H.264 `.mp4`.

## Test GUI

```bash
python gui.py [settings.json]
```

The same "like the wall" view is available in `tools/preview_both.py` with `--projector-gamma 2.2`.

A window for trying things on one computer, without projectors:

- edit the settings (picture or video, resolution, `w`, `d`, gamma, crop or fit) and see the result at once;
- see **both** projectors joined, or only LEFT or only RIGHT;
- turn the **blend** off to compare, and show the **overlap edges**;
- **Like the wall**: adds the light of the two projectors (pixel value ^ projector gamma, 2.2 by default)
  instead of the pixel values, so the preview shows what a real projector pair shows. On the real
  projectors gamma 1.0 left a dark line and gamma 2.0 did not; this view shows the same;
- play, pause and seek a video; it loops;
- open and save settings files, and save the current picture;
- **Start on projector** runs `main.py` for the side you choose (with the shared start time if you typed one), in a separate window, on the
  projector screen. **Stop** closes it.

Wrong settings are shown as a message at the bottom, and the preview keeps the last good picture.
The GUI needs `tkinter`, which comes with most Python installs.

## Smoke test: full-screen on a chosen screen

`display.py` has a manual smoke test at the bottom of the file. It writes a
generated test picture to `images/sample.jpg`, loads it back through
`Image.load`, and shows it full-screen:

```bash
uv run python display.py
```

Press `q` or `ESC` to quit; the window also closes by itself after 30 s, so the
run can never hang unattended.

Edit the `screens` list inside the smoke test to match your desk layout — each
entry is `(x, y, width, height)` in **logical** pixels, and index 0 is the
monitor to show on.

## License

See [LICENSE](LICENSE).
