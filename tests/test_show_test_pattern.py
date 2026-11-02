"""tools/show_test_pattern.py tests (D-44)."""
import numpy as np
import pytest

import tools.show_test_pattern as show_test_pattern


class StubDisplay:
    instances = []

    def __init__(self, *args, **kwargs):
        self.calls = []
        self._key = ord("q")
        StubDisplay.instances.append(self)

    @staticmethod
    def buildTestImage(width=1280, height=720):
        return np.zeros((height, width, 3), dtype=np.uint8)

    def show(self, frame):
        self.calls.append(("show", frame))

    def setFullscreen(self, enabled=True):
        self.calls.append(("setFullscreen", enabled))

    def waitKey(self, delayMs=0):
        self.calls.append(("waitKey", delayMs))
        return self._key

    def close(self):
        self.calls.append(("close",))


@pytest.fixture(autouse=True)
def clear_instances():
    StubDisplay.instances.clear()
    yield


def test_runs_with_default_args(monkeypatch):
    monkeypatch.setattr(show_test_pattern, "Display", StubDisplay)

    assert show_test_pattern.main([]) == 0

    assert len(StubDisplay.instances) == 1
    display = StubDisplay.instances[0]
    names = [call[0] for call in display.calls]
    assert names == ["show", "setFullscreen", "waitKey", "close"]

    shown = display.calls[0][1]
    assert isinstance(shown, np.ndarray)
    assert shown.shape == (720, 1280, 3)


def test_accepts_screen_and_size(monkeypatch):
    monkeypatch.setattr(show_test_pattern, "Display", StubDisplay)

    assert show_test_pattern.main(["--screen", "1", "--width", "1920", "--height", "1080"]) == 0

    shown = StubDisplay.instances[0].calls[0][1]
    assert shown.shape == (1080, 1920, 3)
