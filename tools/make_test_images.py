
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from math_class import MathClass
from setup_class import SetupClass


def main():
    parser = argparse.ArgumentParser(description="Generate projector test images.")
    parser.add_argument("settings", help="Path to settings.json")
    args = parser.parse_args()

    setup = SetupClass()

    try:
        setup.load(args.settings)

        if not setup.validate():
            print("Error: Invalid settings.")
            return 1

        resX, resY = setup.getProjectorResXY()
        w = setup.getImageWidthCm()
        d = setup.getProjectorSpacingCm()

        overlap = MathClass.overlapPx(resX, w, d)
        width = 2 * resX - overlap
        height = resY

        output_dir = Path("test_images")
        output_dir.mkdir(exist_ok=True)

        # 1. Grid image
        grid = np.zeros((height, width, 3), dtype=np.uint8)
        for x in range(0, width, 100):
            cv2.line(grid, (x, 0), (x, height - 1), (255, 255, 255), 1)
        for y in range(0, height, 100):
            cv2.line(grid, (0, y), (width - 1, y), (255, 255, 255), 1)

        cv2.imwrite(str(output_dir / "grid.png"), grid)

        # 2. Horizontal gradient
        gradient_line = np.linspace(0, 255, width, dtype=np.uint8)
        gradient = np.tile(gradient_line, (height, 1))
        gradient = cv2.cvtColor(gradient, cv2.COLOR_GRAY2BGR)

        cv2.imwrite(str(output_dir / "gradient.png"), gradient)

        # 3. Plain white image
        white = np.full((height, width, 3), 255, dtype=np.uint8)

        cv2.imwrite(str(output_dir / "white.png"), white)

        # 4. Alignment marks
        alignment = np.zeros((height, width, 3), dtype=np.uint8)

        points = [
            (50, 50),
            (width - 50, 50),
            (50, height - 50),
            (width - 50, height - 50),
            (width // 2, height // 2),
        ]

        for x, y in points:
            cv2.drawMarker(
                alignment, (x, y), (255, 255, 255),
                cv2.MARKER_CROSS, 40, 2
            )

        cv2.imwrite(str(output_dir / "alignment.png"), alignment)

        print("Generated 4 test images successfully.")
        print(f"Image size: {width} x {height} pixels")
        print(f"Overlap: {overlap} pixels")
        print(f"Saved to: {output_dir.resolve()}")
        return 0

    except (ValueError, FileNotFoundError, OSError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
