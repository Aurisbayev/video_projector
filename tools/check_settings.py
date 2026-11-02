
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setup_class import SetupClass
from side import Side


def main():
    parser = argparse.ArgumentParser(
        description="Check that LEFT and RIGHT projector settings match."
    )
    parser.add_argument("left_file")
    parser.add_argument("right_file")
    args = parser.parse_args()

    try:
        left = SetupClass()
        right = SetupClass()

        left.load(args.left_file)
        right.load(args.right_file)

        if not left.validate():
            print("ERROR: LEFT settings are invalid.")
            return 1

        if not right.validate():
            print("ERROR: RIGHT settings are invalid.")
            return 1

        fields = {
            "projectorResXY": "getProjectorResXY",
            "imageWidthCm": "getImageWidthCm",
            "projectorSpacingCm": "getProjectorSpacingCm",
            "blendCurveGamma": "getBlendCurveGamma",
            "sourcePath": "getSourcePath",
        }

        problems = []

        for field, getter in fields.items():
            left_value = getattr(left, getter)()
            right_value = getattr(right, getter)()

            if left_value != right_value:
                problems.append(
                    f"{field}: LEFT={left_value!r}, RIGHT={right_value!r}"
                )

        if left.getProjectorSide() != Side.LEFT:
            problems.append(
                f"projectorSide: LEFT file has "
                f"{left.getProjectorSide().name}, expected LEFT"
            )

        if right.getProjectorSide() != Side.RIGHT:
            problems.append(
                f"projectorSide: RIGHT file has "
                f"{right.getProjectorSide().name}, expected RIGHT"
            )

        if problems:
            print("ERROR: Settings do not match:")
            for problem in problems:
                print(f"  {problem}")
            return 1

        print("OK: Both settings files are valid and match.")
        print("Only projectorSide differs: LEFT / RIGHT.")
        return 0

    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
