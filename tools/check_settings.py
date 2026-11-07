
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setup_class import SetupClass


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check one settings file, or check that two settings files match."
    )
    parser.add_argument("settings_file")
    parser.add_argument("other_file", nargs="?")
    args = parser.parse_args(argv)

    try:
        first = SetupClass()
        first.load(args.settings_file)

        if not first.validate():
            print(f"ERROR: {args.settings_file} is invalid.")
            return 1

        if args.other_file is None:
            print(f"OK: {args.settings_file} is valid.")
            return 0

        second = SetupClass()
        second.load(args.other_file)

        if not second.validate():
            print(f"ERROR: {args.other_file} is invalid.")
            return 1

        fields = {
            "projectorResXY": "getProjectorResXY",
            "imageWidthCm": "getImageWidthCm",
            "projectorSpacingCm": "getProjectorSpacingCm",
            "blendCurveGamma": "getBlendCurveGamma",
            "sourcePath": "getSourcePath",
            "scaleMode": "getScaleMode",
        }

        problems = []

        for field, getter in fields.items():
            first_value = getattr(first, getter)()
            second_value = getattr(second, getter)()

            if first_value != second_value:
                problems.append(
                    f"{field}: first={first_value!r}, second={second_value!r}"
                )

        if problems:
            print("ERROR: Settings do not match:")
            for problem in problems:
                print(f"  {problem}")
            return 1

        print("OK: Both settings files are valid and match.")
        print(
            f"projectorSide: {first.getProjectorSide().name} / "
            f"{second.getProjectorSide().name} (not compared: --side chooses the side)."
        )
        return 0

    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
