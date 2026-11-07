# Hardware setup {#hardware_setup}

This page covers the physical setup: two projectors, one screen and two
computers, one for each projector. The projectors sit side by side and
their images overlap in the middle. The software blends that overlap, so
the measurements taken here have to match the values in the settings file
that `SetupClass` reads.

Terms used below:

-   `w`: width in centimetres that one projector covers on the screen.
-   `d`: distance in centimetres between the two projectors.
-   Overlap: the part of the screen both projectors light up. Its width is
    `w - d`.
-   Side: `LEFT` or `RIGHT`, as seen from the screen.

## Equipment

| Equipment | Specification | Quantity |
|-----------|---------------|----------|
| Projector | Epson, native resolution 1920 x 1080 | 2 |
| Screen | Any flat screen or wall. The size depends on the room and is not a fixed value: measure `w` and `d` for your setup | 1 |
| Computer | macOS (used in our test) | 2 |
| Video cable | HDMI | 2 |
| Measuring tape | | 1 |

## Layout

<img src="projector_geometry.webp" width="500" alt="Projector geometry and overlap">

Put both projectors at the same height and the same distance from the
screen, one on each side of its centre line. Measure the gap between them
and write it down as `d`.

Then show a test image from one projector at a time and measure its width
on the screen. That is `w`. Move the projectors or change the zoom until
the two images overlap by `w - d` centimetres and their top and bottom
edges line up.

## Connections

Plug each projector into its own computer and set the display mode to
extend, not mirror. Check that the left projector shows the left part of
the image. If the two are swapped, change `projectorSide` in the settings
file or the `--side` option of `main.py`.

## Settings to match

`SetupClass` needs four values from this setup: the projector resolution,
`d`, `w`, and the side for each computer. From these `MathClass`
works out `overlapPx`, the image regions and the mask.

## Check

Show a test image across both projectors. Look at the overlap for a bright
or dark band, and at whether straight lines break where the images meet.
If a band is visible, measure `w` and `d` again before changing `gamma`.

| Symptom | Likely cause |
|---------|--------------|
| Left and right halves swapped | Side set the wrong way round |
| Bright band in the overlap | `w` or `d` differs from the real layout |
| Lines step at the overlap | Projectors not level, or at different distances |
| Only one projector shows an image | Program not running on both computers, or a loose cable |
| Video halves out of step | Started by key press, or computer clocks differ (see @ref software_usage "Software usage") |

Next: @ref software_usage "Software usage".

Back to the @ref index "main page".
