
import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from math_class import MathClass
from setup_class import SetupClass



def find_new_spacing(resX, w, d, direction):
    current = MathClass.overlapPx(resX, w, d)
    target = current + direction

    if not 1 <= target < resX:
        raise ValueError("Overlap cannot move further.")

    # Find a spacing value that produces the requested overlap.
    low = 0.0
    high = w

    for _ in range(60):
        middle = (low + high) / 2

        try:
            calculated = MathClass.overlapPx(resX, w, middle)
        except ValueError:
            calculated = resX if middle <= 0 else 0

        if calculated > target:
            low = middle
        else:
            high = middle

    # Test a small distance on either side of the boundary.
    step = w / (resX * 4)

    for candidate in [low - step, low, high, high + step]:
        if not 0 < candidate < w:
            continue

        try:
            if MathClass.overlapPx(resX, w, candidate) == target:
                return candidate
        except ValueError:
            continue

    raise ValueError("Could not find the requested overlap.")


def save_spacing(path, new_d):
    path = Path(path)
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Change only the selected setting.
    data["projectorSpacingCm"] = new_d

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)

    temp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".settings-",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp_name = temp.name
            json.dump(data, temp, indent=2)
            temp.write("\n")

        # Validate the temporary settings before replacing the original.
        check = SetupClass()
        check.load(temp_name)

        if not check.validate():
            raise ValueError("Adjusted settings failed validation.")

        os.replace(temp_name, path)

    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)

    return backup


def main():
    parser = argparse.ArgumentParser(
        description="Adjust projector overlap using arrow keys."
    )
    parser.add_argument("settings", help="Path to settings JSON")
    args = parser.parse_args()

    setup = SetupClass()
    setup.load(args.settings)

    if not setup.validate():
        print("ERROR: Invalid settings.")
        return 1

    resX = setup.getProjectorResXY()[0]
    w = setup.getImageWidthCm()
    d = setup.getProjectorSpacingCm()

    print("Overlap adjustment")
    print("Right arrow: increase overlap by 1 pixel")
    print("Left arrow: decrease overlap by 1 pixel")
    print("S: save and quit")
    print("Q: quit without saving")

    try:
        import curses

        def handle_keys(screen):
            nonlocal d
            screen.keypad(True)

            while True:
                overlap = MathClass.overlapPx(resX, w, d)
                screen.clear()
                screen.addstr(0, 0, f"Current overlap: {overlap} pixels")
                screen.addstr(1, 0, f"Projector spacing: {d:.8f} cm")
                screen.addstr(3, 0, "LEFT / RIGHT: adjust | S: save | Q: quit")
                screen.refresh()

                key = screen.getch()

                if key == curses.KEY_RIGHT:
                    try:
                        d = find_new_spacing(resX, w, d, 1)
                    except ValueError:
                        pass

                elif key == curses.KEY_LEFT:
                    try:
                        d = find_new_spacing(resX, w, d, -1)
                    except ValueError:
                        pass

                elif key in (ord("s"), ord("S")):
                    return True

                elif key in (ord("q"), ord("Q")):
                    return False

        should_save = curses.wrapper(handle_keys)

        if should_save:
            backup = save_spacing(args.settings, d)
            print(f"Saved projectorSpacingCm: {d:.8f} cm")
            print(f"Backup: {backup}")

            # Confirm the saved settings can be loaded again.
            check = SetupClass()
            check.load(args.settings)
            if not check.validate():
                raise ValueError("Saved settings are invalid.")

            print("OK: Saved settings passed validation.")
        else:
            print("Cancelled. Settings unchanged.")

        return 0

    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
