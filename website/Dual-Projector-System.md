# How a dual-projector system works {#dual_projector_system}

A dual-projector system uses two projectors to display one wide picture on the same screen. Each projector displays one part of the picture. The parts overlap in the middle, and software fades the brightness of each projector through that shared area so the join is less visible.

## The two projectors

Each projector is connected to its own computer. Both computers run the same program and use the same source picture or video and matching projection settings. The only setting that should differ is `projectorSide`:

- The computer connected to the left projector uses `LEFT`.
- The computer connected to the right projector uses `RIGHT`.

The computers do not need to communicate with each other. Each computer independently calculates the part of the combined picture that its projector must display.

## The combined picture and overlap

Each projector covers an image width of `w` centimetres. The distance between the two projectors is `d` centimetres. When the images overlap, the shared width is:

Physical width of overlap = w - d 

The software converts this measurement into pixels using the projector resolution. It then treats the source as one combined image, wide enough to cover both projectors and their overlap.

Each computer selects its own horizontal slice from that combined image. The left slice covers the left side and part of the center; the right slice covers part of the center and the right side. The center portion is therefore displayed by both projectors.

## How the fade works

If both projectors displayed the overlap at full brightness, the shared area would appear brighter than the rest of the picture. The software applies a **blending mask** to reduce each projector's brightness across the overlap.

\image html fade-overlap.svg "Brightness fades applied by the left and right projectors across their shared overlap" width=700px

The left projector's mask fades from full brightness (1) to zero (0) across the overlap. The right projector's mask fades in the opposite direction, from zero (0) to full brightness (1). Outside the overlap, each projector displays its own area at full brightness.

In our testing, the two fades are complementary when the blend gamma is set to 2.0, producing an even join across the overlap on the real projectors. A gamma of 1.0 leaves a dark line in the middle because projector brightness is not directly proportional to pixel value. 

The blendCurveGamma setting adjusts the shape of the fade and should be tuned only after the projectors are physically aligned and the measurements are correct.

## What the software does on each computer

1. Loads and validates the projection settings.
2. Loads the same source picture or video used by the other computer.
3. Calculates the overlap, the image slice for its `projectorSide`, and the blending mask.
4. Resizes the source to the combined image dimensions.
5. Crops the slice assigned to that projector.
6. Applies the blending mask to the slice.
7. Displays the processed slice full-screen on the connected projector.

Because both computers use the same source, dimensions, measurements, and blend settings, their two projected slices line up to form one wide picture.

## Physical setup matters

The software can blend the overlap, but it cannot correct every physical alignment problem. The projectors should be at the same height and distance from the screen, use matching zoom settings, and produce images with aligned top and bottom edges. Measure the projected width and the distance between image centers accurately.

For equipment, connections, measurements, and alignment checks, see @ref hardware_setup "Hardware setup". For installing and running the program, see @ref software_usage "Software usage".

Back to the @ref mainpage "main page".
