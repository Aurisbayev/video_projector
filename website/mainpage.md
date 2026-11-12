# Dual-Projector Projection System {#mainpage}

The **Dual-Projector Projection System** uses two computers and two projectors to show one continuous picture or video across a screen. Each computer renders one side of the same combined image. The projected images overlap in the center, where brightness masks reduce the contribution from each projector to create a smoother join.

This documentation covers the physical arrangement, software installation, configuration, operation, and the Python API.

For a step-by-step explanation of the two projectors, their shared image area, and the brightness fade, see @ref dual_projector_system "How a dual-projector system works".

## How the system works

1. Both computers load the same source picture or video and compatible projection settings.
2. The software scales the source to the dimensions of the combined projection.
3. Each computer selects the horizontal region assigned to its projector.
4. A blending mask adjusts the brightness across the overlap.
5. Each computer displays its own region full-screen on its connected projector.

The computers must use matching geometry and source settings. Their `projectorSide` values must differ: one computer is `LEFT`, and the other is `RIGHT`.

## Key terms

| Term | Meaning |
|---|---|
| `w` | Width in centimetres covered by one projector on the screen. |
| `d` | Distance in centimetres between the two projectors. |
| Overlap | Screen area illuminated by both projectors; its width is `w - d`. |
| `overlapPx` | Overlap width in pixels in the combined image. |
| `Region` | A horizontal image slice, described by its starting x-coordinate and width. |
| `Mask` | Per-column brightness multipliers, from `0` (black) to `1` (full brightness). |
| Blend `gamma` | The setting that shapes the brightness fade through the overlap. |
| Frame | One image in a video. |
| `fps` | Video frame rate, in frames per second. |
| Shared start time | A local clock time at which both computers are scheduled to begin video playback. |
| `crop` / `fit` | The two source-image scaling modes: fill the combined image and crop excess, or show the whole image with black bars. |

The `blendCurveGamma` setting is not the same as a projector's physical gamma response.

## Projector geometry

The two projectors are positioned side by side. Each covers a width `w`; the distance between them is `d`. The geometry calculations use these measurements and the projector resolution to determine the overlap in pixels and the region shown by each side.

The illustration below shows the combined image and its left, overlap, and right portions.

\image html combined-image-example.svg "Combined image and overlap geometry" width=700px

For the physical arrangement and measurement procedure, see @ref hardware_setup "Hardware setup".

## Main classes

- **`PipelineClass`** coordinates the processing and display pipeline for pictures and videos.
- **`SetupClass`** loads and validates the JSON settings, including resolution, screen measurements, blend gamma, source path, projector side, and scaling mode.
- **`MathClass`** calculates projection geometry, overlap width in pixels, image regions, and blending masks.
- **`VideoSource`** reads video frames and provides timing information for playback.
- **`Region`** represents a horizontal slice of an image using its x-coordinate and width.
- **`Mask`** stores brightness multipliers used during blending.
- **`Side`** identifies the left (`LEFT`) or right (`RIGHT`) projector.

The UML class diagram shows the principal classes and their relationships. Module-level functions, command-line entry points, test utilities, and some supporting modules are not represented.

<a href="MainDiagram.png"><img src="MainDiagram.png" width="100%" alt="UML class diagram"></a>

## Pictures and videos

The `sourcePath` setting selects the source file. The file extension determines whether the program treats it as a picture or a video.

For pictures, `scaleMode` controls how the source is fitted to the combined image:

- **`crop`** (default): fills the combined image and cuts off the excess at the edges. The picture is not stretched.
- **`fit`**: shows the complete picture and adds black bars where needed. The picture is not stretched.

For videos, each computer selects frames using the playback clock rather than simply advancing one frame after another. If a computer is slow, it can skip a frame instead of falling progressively behind. Playback loops when the video ends and has no audio.

A video can start after a key press or at a shared local time supplied with `--start-at`. For synchronized playback, both computers need the same start time, clock, and time zone. See @ref software_usage "Software usage".

Press `q` or `Esc` to stop playback. If OpenCV cannot open a video, try re-encoding it as H.264 in an `.mp4` file.

## Included tools

- **`main.py`** runs the projection program for one computer and one projector side.
- **`instant_run.py`** provides a short command for a projector run, a joined preview, or the test GUI.
- **`gui.py`** provides a test window for editing settings, previewing both sides together, and starting the projection program.
- **`tools/preview_both.py`** previews the joined output from both projector sides.
- **`tools/make_test_video.py`** creates a test video with a moving bar for checking the image and overlap.
- **`display.py`** contains the display handling and a small display smoke test.

## Blending and gamma

The blending mask controls the brightness contributed by each projector in the overlap. The `blendCurveGamma` setting changes the shape of the fade. It should be adjusted only after the projectors are positioned, aligned, and measured correctly.

A projector's physical light output is not necessarily proportional to the pixel value. The preview tools provide a separate **Like the wall** view that approximates this response using a projector-gamma value. That preview calculation is for visual comparison; it is not the blending algorithm used by the projection pipeline. A value around `2.2` is a common approximation, not a measured property of the projectors used in testing.

Do not confuse:

- **Blend gamma** (`blendCurveGamma`): shapes the overlap fade in the application.
- **Projector gamma** (`--projector-gamma` in the preview tool): approximates how pixel values translate into projected light in the preview.

## Documentation navigation

Use the Doxygen class and file lists to explore the API. Start with `MathClass` for projection calculations, `SetupClass` for settings and validation, or `PipelineClass` for the processing sequence.

For installation and command examples, continue to @ref software_usage "Software usage". For the physical setup, see @ref hardware_setup "Hardware setup". Downloads and project links are on @ref downloads "Downloads".
