# Downloads and project resources {#downloads}

This page links to the project source, generated API documentation, and the tools used to build that documentation.

## Project source code

The source repository contains the Python application, example settings, test images, test suite, and documentation source files.

- [Browse the GitHub repository](https://github.com/maksym-syd/video_projector)
- [Download the main branch as a ZIP archive](https://github.com/maksym-syd/video_projector/archive/refs/heads/main.zip)

To run the application, download or clone the repository and follow @ref software_usage "Software setup and usage". The generated test video is not included in the repository; create it locally using `tools/make_test_video.py`.

## Generated Doxygen documentation

The HTML documentation describes the system design, classes, methods, and source files.

Click on Classes in the header bar to view.

The HTML pages are generated from the documentation comments and Markdown files in the repository. The generated website output is not stored in the source repository (You can find it in ./website).

## Doxygen

[Doxygen](https://www.doxygen.nl/) extracts documentation from source code comments and Markdown files. It can generate HTML documentation and other output formats.

- [Download Doxygen](https://www.doxygen.nl/download.html)
- [Doxygen installation instructions](https://www.doxygen.nl/manual/install.html)
- [Doxygen project website](https://www.doxygen.nl/)

Choose the package for your operating system and processor architecture. After installing Doxygen, open the project's `Doxyfile` in the Doxygen GUI and run **Run doxygen**, or run the following command from the repository root:

```bash
doxygen Doxyfile
```

The generated HTML site is written to `website/html/`. Open `website/html/index.html` in a web browser.

## Main project components

| Component | Responsibility |
|---|---|
| `PipelineClass` | Coordinates the picture and video processing pipeline. |
| `SetupClass` | Loads and validates the projection settings. |
| `MathClass` | Calculates projection dimensions, overlap pixels, image regions, and blending masks. |
| `VideoSource` | Opens a video and provides frames and playback timing. |
| `Region` | Describes a horizontal image region by its starting x-coordinate and width. |
| `Mask` | Stores the brightness multipliers used in the overlap. |
| `Side` | Identifies the `LEFT` and `RIGHT` projector sides. |

For installation, configuration, and run instructions, see @ref software_usage "Software setup and usage". For the physical projector arrangement, see @ref hardware_setup "Hardware setup".
