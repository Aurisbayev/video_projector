
# Dual-Projector Projection System {#downloads}

Welcome to the download page for the **Dual-Projector Projection System**.

This page provides access to the project documentation, source code,
and the tools required to generate and view the documentation.

---

## Doxygen Documentation

The Doxygen documentation provides detailed information about the
system architecture, class relationships, and implementation.

Use the documentation to understand how the projection geometry,
image regions, and blending masks work together.

[**Open Doxygen Documentation**](@ref index)

---

## GitHub Repository

The GitHub repository contains the source code and project files
used to implement the Dual-Projector Projection System.

You can browse the source code, review the implementation, and
download the project files for local use.

[**Open GitHub Repository**](https://github.com/maksym-syd/video_projector)

[**Download Project Files (.zip)**](https://github.com/maksym-syd/video_projector/archive/refs/heads/main.zip)

---

## Download Doxygen

Doxygen is a documentation generation tool that extracts information
from source code and generates structured documentation in HTML
and other formats.

To generate or update the documentation locally, download Doxygen
for your operating system from the official website.

[**Download Doxygen**](https://www.doxygen.nl/download.html)

Available downloads include installers or packages for Windows,
macOS, and Linux.

---

## Installing Doxygen

Follow the instruction page in the link below to install Doxygen and prepare your
environment for generating project documentation.

Open the official download page and select the package
appropriate for your operating system and processor.

[Doxygen Installation Guide](https://www.doxygen.nl/manual/install.html).

## Additional Resources

- [Official Doxygen Website](https://www.doxygen.nl/)
- [Doxygen Download Page](https://www.doxygen.nl/download.html)
- [Doxygen Installation Guide](https://www.doxygen.nl/manual/install.html)
- [Official Doxygen GitHub Repository](https://github.com/doxygen/doxygen)

---

## Project Classes

The documentation covers the main components of the
Dual-Projector Projection System.

- **PipelineClass:** Coordinates the pipeline for pictures and videos.
- **SetupClass:** Loads and validates projector and system settings.
- **MathClass:** Calculates projection geometry, overlap pixels,
  image regions, and blending masks.
- **VideoSource:** Reads a video file one frame at a time.
- **Region:** Represents a horizontal image region using its
  starting pixel and width.
- **Mask:** Stores brightness multipliers for blending.
- **Side:** Identifies the left or right projector.

For more details about each class and its methods, visit the
[Doxygen Documentation](@ref index).

---