# Hardware setup {#hardware_setup}

This page describes the physical arrangement required by the dual-projector system. The setup uses two projectors, one screen or flat wall, and two computers. Each computer drives one projector.

The two projected images must have the same height and align at their top and bottom edges. They must also overlap by the amount expected by the software. Incorrect measurements or alignment can produce a visible seam even when the blending settings are correct.

## Equipment

| Equipment | Specification | Quantity |
|---|---|---:|
| Projector | Epson projectors, native resolution 1920 × 1080 in the tested setup | 2 |
| Screen | Flat projection screen or wall; dimensions depend on the room | 1 |
| Computer | One computer for each projector; macOS was used for testing | 2 |
| Video cable | HDMI, compatible with the computer and projector | 2 |
| Measuring tape | For measuring the projected width and spacing | 1 |

Other projector models and operating systems may work, but their resolution and display behaviour should be checked before calibration.

## Projector arrangement

\image html system-dimensions.svg "Projector and screen dimensions" width=700px

Place the projectors side by side, at the same height and at the same distance from the screen. Aim them so that their projected images overlap in the centre. Avoid keystone correction where possible; physically align the projectors and use matching zoom settings to keep the image geometry consistent.

The geometry model uses these measurements:

- **`w` — projection width:** the width, in centimetres, covered on the screen by one projector.
- **`d` — projector spacing:** the distance, in centimetres, between the centres of the two projected images.
- **Overlap:** the shared illuminated width, calculated as `w - d`.

Measure `w` by displaying an image from one projector at a time. Measure `d` between the centres of the two projected images, using the same reference points for both. Record the measurements in centimetres.

The two images should have equal width and height. Adjust projector position and zoom until the overlap matches `w - d` and the top and bottom edges line up.

## Connect the computers

1. Connect each projector to its own computer using HDMI.
2. In the operating system's display settings, choose an extended desktop rather than mirroring the displays.
3. Confirm which display is connected to the left projector and which is connected to the right projector.
4. Set the correct `projectorSide` for each computer: `LEFT` on the left and `RIGHT` on the right.

If the sides are reversed, change the `projectorSide` value in the settings JSON file or use the `--side` command-line option when starting `main.py`.

## Values required by the software

The settings file on each computer must describe the same physical arrangement and source:

| Setting | What to enter |
|---|---|
| `projectorResXY` | Native projector resolution as `[width, height]`, in pixels. |
| `imageWidthCm` | Measured single-projector image width, `w`, in cm. |
| `projectorSpacingCm` | Measured distance between projectors `d`, in cm. |
| `projectorSide` | `LEFT` on one computer and `RIGHT` on the other. |
| `blendCurveGamma` | Blend-curve setting. Start with the same value on both computers. |
| `sourcePath` | Same picture or video source on both computers. |
| `scaleMode` | Same source scaling mode on both computers: `crop` or `fit`. |

`MathClass` uses the resolution and measurements to calculate the overlap in pixels, the image region assigned to each projector, and the blending mask. Do not estimate `overlapPx` manually; it is derived from the settings.

For the JSON format and example commands, see @ref software_usage "Software usage".

## Alignment check

Before testing a full picture or video:

1. Display a grid or other test image across both projectors.
2. Check that the top and bottom edges align.
3. Check that straight horizontal and vertical lines continue across the join.
4. Look for a bright or dark band in the overlap.
5. If the join is visibly displaced, recheck the physical alignment and measurements before changing the blend gamma.

The repository includes test images and a test-video generator. The software setup page explains how to run them.

## Troubleshooting

| Symptom | Possible cause and check |
|---|---|
| Left and right portions are swapped | Check `projectorSide` or the `--side` option. |
| Bright or dark band in the overlap | Recheck `w`, `d`, zoom, and image alignment before adjusting `blendCurveGamma`. |
| A line is broken or stepped at the join | The projectors may be at different heights, distances, or zoom levels. Re-align them. |
| Only one projector displays an image | Check that the program is running on both computers, that each side is assigned correctly, and that both HDMI connections work. |
| Video portions are out of sync | Use the same `--start-at` time on both computers and check that their clocks and time zones agree. See @ref software_usage "Software usage". |

Next: @ref software_usage "Software usage".

Back to the @ref mainpage "main page".
