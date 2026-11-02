"""PipelineClass.run tests (D-21)."""
import numpy as np
import pytest

import pipeline_class
from image import Image
from pipeline_class import PipelineClass


class RecordingDisplay:
    instances = []

    def __init__(self, *args, **kwargs):
        self.calls = []
        RecordingDisplay.instances.append(self)

    def show(self, frame):
        self.calls.append(("show", frame))

    def setFullscreen(self, enabled=True):
        self.calls.append(("setFullscreen", enabled))

    def waitKey(self, delayMs=0):
        self.calls.append(("waitKey", delayMs))
        return ord("q")

    def close(self):
        self.calls.append(("close",))


@pytest.fixture
def recordingDisplay(monkeypatch):
    RecordingDisplay.instances.clear()
    monkeypatch.setattr(pipeline_class, "Display", RecordingDisplay)
    return RecordingDisplay


def test_steps_run_in_order_exactly_once(makePipeline, monkeypatch):
    p = makePipeline()
    order = []
    for name in ("load", "scaleSource", "crop", "applyMask", "display"):
        original = getattr(p, name)

        def spy(*args, _name=name, _original=original, **kwargs):
            order.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(p, name, spy)
    monkeypatch.setattr(pipeline_class, "Display", RecordingDisplay)
    p.run()
    assert order == ["load", "scaleSource", "crop", "applyMask", "display"]


@pytest.mark.parametrize("side", ["LEFT", "RIGHT"])
def test_run_shows_this_sides_masked_slice(makePipeline, recordingDisplay, side):
    p = makePipeline(side, resXY=(200, 60), d=89.5)
    p.run()
    assert len(recordingDisplay.instances) == 1
    shown = recordingDisplay.instances[0].calls[0][1]
    assert isinstance(shown, np.ndarray)
    assert shown.shape == (60, 200, 3) and shown.dtype == np.uint8
    assert isinstance(p._PipelineClass__output, Image)


def test_run_with_missing_source_raises(makePipeline, recordingDisplay, tmp_path):
    p = makePipeline()
    (tmp_path / "source.png").unlink()
    with pytest.raises(FileNotFoundError):
        p.run()
    assert recordingDisplay.instances == []
