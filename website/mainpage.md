# Dual-Projector Projection System {#mainpage}

Welcome to the documentation for the **Dual-Projector Projection
System**.

This project coordinates two projectors to display a combined picture
or video across a screen. Each projector is driven by its own computer.
The projected regions overlap, and a blending mask adjusts brightness in
that overlap to make the combined image appear more continuous.

## System overview

The system uses the projector configuration, screen geometry, and
selected projector side to determine which part of the combined image
each projector displays. A blending mask controls the brightness of
pixels in the overlap region.

Key terms:

-   **Projection width (`w`)**: width, in centimetres, covered by one
    projector on the screen.
-   **Projector spacing (`d`)**: distance, in centimetres, between the
    two projectors.
-   **Overlap**: screen region illuminated by both projectors.
-   **`overlapPx`**: overlap width expressed as a whole number of
    pixels.
-   **Region**: the horizontal part of the combined image assigned to
    one projector.
-   **Mask**: a list of brightness multipliers from `0` (black) to `1`
    (full brightness).
-   **Gamma (`gamma`)**: parameter that shapes the brightness fade
    across the overlap.
-   **Frame**: one picture of a video.
-   **Frame rate (`fps`)**: number of video frames per second [frames
    per second].
-   **Frame number**: position of a frame in the video, counted from
    `0`.
-   **Shared start time**: the moment both computers start a video,
    given as the same clock time on both.
-   **Crop / fit**: the two `scaleMode` values: fill and cut the edges /
    show everything with black bars.
-   **Slice**: the picture cut out of the combined image for this
    computer's projector, `resX` wide [px].
-   **Projector gamma**: how strongly a projector's light grows with the
    pixel value, about `2.2`. Not the same as gamma in the settings,
    which shapes the fade.

## UML class diagram

The diagram below shows the main classes, their relationships, and the
methods documented in this project. The module functions
(`parseStartTime`, `findProjectorScreens`, `screenRects`), `main.py`,
the test window and the tools are not on the diagram.

<a href="MainDiagram.png"><img src="MainDiagram.png" width="100%" alt="UML Class Diagram"></a>

## Projector geometry and blending

This digital illustration summarizes the two-projector arrangement, the
overlap on the screen, the opposing brightness fades, and how the
combined image is divided into left, overlap, and right regions.

<img src="projector_geometry.webp" width="500" alt="Projector Geometry">

## Main classes

-   **`PipelineClass`** coordinates the pipeline for pictures and
    videos.
-   **`SetupClass`** loads and validates settings such as projector
    resolution, image width, projector spacing, blending gamma, source
    path, projector side, and scale mode (`crop` or `fit`).
-   **`MathClass`** calculates overlap width, total projection width,
    pixel density, overlap pixels, image regions, and blending masks.
-   **`VideoSource`** reads a video file one frame at a time.
-   **`Region`** represents a horizontal region using its starting pixel
    and width.
-   **`Mask`** stores per-column brightness multipliers.
-   **`Side`** identifies the left (`LEFT = 1`) or right (`RIGHT = 2`)
    projector.

## Video

The setting `sourcePath` can be a picture or a video. The file extension
decides which one it is.

A video is played frame by frame. Each computer picks the frame from the
clock, so a slow computer skips frames and does not fall behind.

A video starts on a key press, or at a shared start time that both
computers get with the option `--start-at`. It loops at the end and
stops with `q` or `Esc`. There is no sound.

If a video file does not open, re-encode it as H.264 `.mp4`.

## Picture proportions

The setting `scaleMode` says how the source is fitted to the combined
image. Neither mode stretches the picture.

-   **`crop`** (default) fills the combined image. It cuts the edges and
    keeps the centre.
-   **`fit`** shows the whole picture in the centre with black bars.

An example: the combined image is about 3.2 times as wide as it is high.
A 16:9 video is about 1.8 times as wide as it is high. So `crop` loses
about 45 percent of the height of the video, while `fit` shows
everything with bars on the left and right.

## Tools

-   **`gui.py`** is a test window to edit the settings, see both
    projectors joined, compare with and without the blend, play a video,
    and start the real show.
-   **`tools/preview_both.py`** shows a joined preview of pictures and
    videos.
-   **`tools/make_test_video.py`** writes a test video with a sweeping
    bar.

## Blend test on the real projectors

Two Epson projectors showed the dice picture. With gamma `1.0` a faint
dark line is visible in the middle, where the two projections overlap.
With gamma `2.0` no line is visible.

The reason is that a projector does not give light in proportion to the
pixel value. The light follows about `pixel ^ 2.2`. With gamma `1.0` the
two linear fades add up to less than full light in the middle of the
overlap, so a dark band appears. With gamma `2.0` they add up to about
full light.

The preview tools reproduce this with the light view:

-   For each pixel, `light = (value / 255) ^ G`.
-   The two lights are added.
-   The sum is limited to `1` and turned back with `^ (1 / G)`.

This is done only in the overlap. It is a preview-only calculation and
is not used when projecting. The value `2.2` is typical. It was not
measured for these projectors.

Do not mix up the two gammas:

-   **`gamma` / `blendCurveGamma`** is a setting that shapes the fade.
    Its range of `0.5` to `3.0` is not final yet.
-   **Projector gamma** (`--projector-gamma`, "Like the wall") is a
    property of the projector.

## Documentation navigation

Use the class list and file list generated by Doxygen to browse the API
documentation. Start with `MathClass` for geometry and mask
calculations, or `SetupClass` for configuration loading and validation.
