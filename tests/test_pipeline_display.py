"""PipelineClass.display tests (D-20)."""
import numpy as np
import pytest

from image import Image
import pipeline_class
from conftest import StubSetup
from pipeline_class import PipelineClass


class StubDisplay:
    instances = []

    def __init__(self, *args, **kwargs):
        self.calls = []
        self._key = ord("q")
        StubDisplay.instances.append(self)

    def show(self, frame):
        self.calls.append(("show", frame))

    def setFullscreen(self, enabled=True):
        self.calls.append(("setFullscreen", enabled))

    def waitKey(self, delayMs=0):
        self.calls.append(("waitKey", delayMs))
        return self._key

    def close(self):
        self.calls.append(("close",))


def _image_from_array(array):
    image = Image()
    image.setFrame(array)
    return image


def test_display_shows_fullscreen_and_closes(monkeypatch):
    StubDisplay.instances.clear()
    monkeypatch.setattr(pipeline_class, "Display", StubDisplay)

    pipeline = PipelineClass(StubSetup())
    array = np.zeros((100, 200, 3), np.uint8)
    frame = _image_from_array(array)
    pipeline.display(frame)

    assert pipeline._PipelineClass__output is frame
    assert len(StubDisplay.instances) == 1
    display = StubDisplay.instances[0]

    names = [call[0] for call in display.calls]
    assert names == ["show", "setFullscreen", "waitKey", "close"]
    assert display.calls[0][1] is array
    assert display.calls[1][1] is True
    assert display.calls[2][1] == 0


def test_display_raises_for_non_image(monkeypatch):
    StubDisplay.instances.clear()
    monkeypatch.setattr(pipeline_class, "Display", StubDisplay)

    pipeline = PipelineClass(StubSetup())
    with pytest.raises(ValueError):
        pipeline.display("not a frame")

    assert len(StubDisplay.instances) == 0


def test_display_raises_for_empty_image(monkeypatch):
    StubDisplay.instances.clear()
    monkeypatch.setattr(pipeline_class, "Display", StubDisplay)

    pipeline = PipelineClass(StubSetup())
    with pytest.raises(ValueError):
        pipeline.display(Image())

    assert len(StubDisplay.instances) == 0
