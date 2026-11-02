"""Projector screen detection and the side setter."""
import pytest

import display
from conftest import StubSetup
from setup_class import SetupClass
from side import Side


def test_screen_rects_primary_only():
    assert display.screenRects([(0, 0, 1470, 956)]) == [(0, 0, 1470, 956)]


def test_screen_rects_projector_to_the_right():
    rects = display.screenRects([(0, 0, 1470, 956), (1470, 0, 1920, 1080)])
    # macOS y grows upwards, the window y grows downwards: the taller projector
    # starts 124 px above the primary screen's top edge.
    assert rects == [(0, 0, 1470, 956), (1470, -124, 1920, 1080)]


def test_projector_is_the_second_screen(monkeypatch):
    class Frame:
        def __init__(self, x, y, w, h):
            self.origin = type("P", (), {"x": x, "y": y})()
            self.size = type("S", (), {"width": w, "height": h})()

    class Screen:
        def __init__(self, *frame):
            self._frame = Frame(*frame)

        def frame(self):
            return self._frame

    class FakeAppKit:
        class NSScreen:
            @staticmethod
            def screens():
                return [Screen(0, 0, 1470, 956), Screen(1470, 0, 1920, 1080)]

    monkeypatch.setitem(__import__("sys").modules, "AppKit", FakeAppKit)
    screens, index = display.findProjectorScreens()
    assert index == 1 and len(screens) == 2


def test_single_screen_uses_the_primary(monkeypatch):
    class FakeAppKit:
        class NSScreen:
            @staticmethod
            def screens():
                class F:
                    origin = type("P", (), {"x": 0, "y": 0})()
                    size = type("S", (), {"width": 1470, "height": 956})()
                return [type("Sc", (), {"frame": staticmethod(lambda: F)})()]

    monkeypatch.setitem(__import__("sys").modules, "AppKit", FakeAppKit)
    screens, index = display.findProjectorScreens()
    assert index == 0 and len(screens) == 1


def test_screens_cannot_be_read_returns_none(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "AppKit", None)
    assert display.findProjectorScreens() == (None, 0)


def test_set_projector_side(makeSettings):
    setup = SetupClass()
    setup.load(makeSettings(side="LEFT"))
    setup.setProjectorSide(Side.RIGHT)
    assert setup.getProjectorSide() is Side.RIGHT


@pytest.mark.parametrize("bad", ["RIGHT", 2, None])
def test_set_projector_side_rejects_non_side(makeSettings, bad):
    setup = SetupClass()
    setup.load(makeSettings())
    with pytest.raises(ValueError):
        setup.setProjectorSide(bad)
