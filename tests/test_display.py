"""Tests for the logic of the Display class. No GUI window is ever opened.

Only the validation error paths of show() are exercised; cv2.namedWindow /
cv2.imshow / cv2.waitKey / cv2.destroyWindow are never called (the tests confirm
that the calls fail while no window exists).
"""
import pytest

from display import Display

SCREENS = [(0, 0, 1920, 1080), (1920, 0, 1280, 720)]


def state(display):
    """Test-only: peek at private attributes directly (to avoid growing the public API)."""
    return {
        "windowOpen": display._Display__windowOpen,
        "fullscreen": display._Display__fullscreen,
        "screen": display._Display__screen,
        "screens": display._Display__screens,
        "windowName": display._Display__windowName,
    }


class TestConstructor:
    def test_defaults(self):
        display = Display()
        assert state(display)["windowName"] == "projector"
        assert state(display)["screens"] is None
        assert state(display)["screen"] == 0
        assert display.isFullscreen() is False
        assert state(display)["windowOpen"] is False

    def test_accepts_valid_screens(self):
        display = Display(windowName="proj", screens=SCREENS, screen=1)
        assert state(display)["windowName"] == "proj"
        assert state(display)["screens"] == SCREENS
        assert state(display)["screen"] == 1

    def test_accepts_list_entries_and_tuple_container(self):
        # Accepts either (list, tuple) entries and normalises them to tuples internally
        display = Display(screens=((0, 0, 800, 600), [800, 0, 800, 600]))
        assert state(display)["screens"] == [(0, 0, 800, 600), (800, 0, 800, 600)]

    def test_empty_screens_is_none(self):
        display = Display(screens=[])
        assert state(display)["screens"] is None
        assert state(display)["screen"] == 0

    @pytest.mark.parametrize("windowName", ["", "   ", "\t\n", None, 5, b"proj"])
    def test_invalid_window_name_raises(self, windowName):
        with pytest.raises(ValueError):
            Display(windowName=windowName)

    @pytest.mark.parametrize(
        "screens",
        [
            "1920x1080",
            b"1920x1080",
            1920,
            {"x": 0},
            [(0, 0, 1920)],
            [(0, 0, 1920, 1080, 1)],
            [(0, 0, 0, 1080)],
            [(0, 0, 1920, 0)],
            [(0, 0, -1920, 1080)],
            [(0, 0, 1920.0, 1080)],
            [(0, 0, True, 1080)],
            [("0", 0, 1920, 1080)],
            ["0,0,1920,1080"],
            [None],
        ],
    )
    def test_invalid_screens_raise(self, screens):
        with pytest.raises(ValueError):
            Display(screens=screens)

    @pytest.mark.parametrize("screen", [2, 3, -1])
    def test_out_of_range_screen_raises(self, screen):
        with pytest.raises(IndexError):
            Display(screens=SCREENS, screen=screen)

    @pytest.mark.parametrize("screen", ["0", 0.0, None, True])
    def test_non_int_screen_raises(self, screen):
        with pytest.raises(ValueError):
            Display(screens=SCREENS, screen=screen)


class TestSetScreen:
    def test_in_range(self):
        display = Display(screens=SCREENS)
        display.setScreen(1)
        assert state(display)["screen"] == 1
        display.setScreen(0)
        assert state(display)["screen"] == 0

    @pytest.mark.parametrize("index", [2, 10, -1])
    def test_out_of_range_raises(self, index):
        display = Display(screens=SCREENS)
        with pytest.raises(IndexError) as excinfo:
            display.setScreen(index)
        # The message reports the number of configured monitors
        assert "2" in str(excinfo.value)
        # A failure keeps the previous selection
        assert state(display)["screen"] == 0

    def test_without_screens_raises(self):
        display = Display()
        with pytest.raises(IndexError) as excinfo:
            display.setScreen(0)
        assert "0" in str(excinfo.value)

    @pytest.mark.parametrize("index", ["0", 0.0, None, True])
    def test_non_int_index_raises(self, index):
        with pytest.raises(ValueError):
            Display(screens=SCREENS).setScreen(index)


class TestFullscreen:
    def test_default_is_false(self):
        assert Display().isFullscreen() is False

    def test_before_show_raises(self):
        with pytest.raises(RuntimeError):
            Display().setFullscreen(True)

    def test_before_show_raises_with_explicit_false(self):
        with pytest.raises(RuntimeError):
            Display().setFullscreen(False)

    def test_before_show_keeps_state(self):
        display = Display()
        with pytest.raises(RuntimeError):
            display.setFullscreen(True)
        assert display.isFullscreen() is False
        assert state(display)["windowOpen"] is False


class TestShowValidation:
    @pytest.mark.parametrize(
        "frame", [None, "frame", 0, 1.0, [], [[1, 2, 3]], (255, 255, 255)]
    )
    def test_non_ndarray_frame_raises(self, frame):
        display = Display(screens=SCREENS)
        with pytest.raises(ValueError):
            display.show(frame)
        # Validation runs first, so no window has been created
        assert state(display)["windowOpen"] is False

    def test_non_ndarray_frame_does_not_create_window(self):
        display = Display()
        with pytest.raises(ValueError):
            display.show(object())
        assert state(display)["windowOpen"] is False


class TestClose:
    def test_close_without_show_is_noop(self):
        display = Display()
        display.close()
        display.close()
        assert state(display)["windowOpen"] is False

    def test_double_close_after_failed_show(self):
        display = Display()
        with pytest.raises(ValueError):
            display.show(None)
        display.close()
        display.close()


class TestWindowMode:
    def test_fullscreen_mode_constant(self):
        display = Display()
        assert display._Display__windowMode(True) != display._Display__windowMode(False)
