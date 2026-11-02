"""PipelineClass.load tests (D-17)."""
import json

import cv2
import numpy as np
import pytest

from image import Image
from pipeline_class import PipelineClass
from setup_class import SetupClass

HEIGHT = 24
WIDTH = 32


def make_pipeline(tmp_path, sourceName):
    settingsPath = tmp_path / "settings.json"
    settingsPath.write_text(json.dumps({
        "projectorResXY": [1920, 1080],
        "imageWidthCm": 100.0,
        "projectorSpacingCm": 80.0,
        "blendCurveGamma": 1.0,
        "sourcePath": sourceName,
        "projectorSide": "LEFT",
    }), encoding="utf-8")
    setup = SetupClass()
    setup.load(str(settingsPath))
    p = PipelineClass(setup)
    # Until D-43 the constructor does not store setup; set it as test_scale_source.py does.
    p._PipelineClass__setup = setup
    return p


def test_good_image_fills_source_frame(tmp_path):
    written = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
    written[:, :, 1] = 255
    written[0, 0] = (10, 20, 30)
    assert cv2.imwrite(str(tmp_path / "source.png"), written)
    p = make_pipeline(tmp_path, "source.png")

    out = p.load()

    assert isinstance(out, Image)
    assert out.getFrame().dtype == np.uint8
    assert out.getShape() == (HEIGHT, WIDTH, 3)
    assert np.array_equal(out.getFrame(), written)
    assert p._PipelineClass__sourceFrame is out


def test_missing_image_raises_file_not_found(tmp_path):
    p = make_pipeline(tmp_path, "missing.png")
    with pytest.raises(FileNotFoundError) as excinfo:
        p.load()
    assert "missing.png" in str(excinfo.value)


def test_file_that_is_not_a_picture_raises_value_error(tmp_path):
    (tmp_path / "notapicture.png").write_bytes(b"this is not an image")
    p = make_pipeline(tmp_path, "notapicture.png")
    with pytest.raises(ValueError) as excinfo:
        p.load()
    assert "notapicture.png" in str(excinfo.value)
