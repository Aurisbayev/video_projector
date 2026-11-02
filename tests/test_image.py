"""Tests for the Image class (a wrapper around cv2.imread). No GUI window is ever opened."""
import cv2
import numpy as np
import pytest

from image import Image

HEIGHT = 24
WIDTH = 32


@pytest.fixture()
def sample_path(tmp_path):
    """Write an all-green PNG and return its path."""
    path = tmp_path / "sample.png"
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    frame[:, :, 1] = 255  # Set only G in BGR
    assert cv2.imwrite(str(path), frame) is True
    return path


class TestLoad:
    def test_returns_ndarray(self, sample_path):
        image = Image()
        frame = image.load(str(sample_path))
        assert isinstance(frame, np.ndarray)
        assert frame.dtype == np.uint8

    def test_shape(self, sample_path):
        frame = Image().load(str(sample_path))
        assert frame.shape == (HEIGHT, WIDTH, 3)

    def test_reads_bgr_channels(self, sample_path):
        # An image written as green reads back as G=255 / B=R=0 (BGR check)
        frame = Image().load(str(sample_path))
        blue, green, red = frame[0, 0]
        assert (int(blue), int(green), int(red)) == (0, 255, 0)

    def test_missing_path_raises(self, tmp_path):
        missing = tmp_path / "does_not_exist.png"
        with pytest.raises(FileNotFoundError) as excinfo:
            Image().load(str(missing))
        assert str(missing) in str(excinfo.value)

    def test_directory_raises(self, tmp_path):
        # Exists but is not a file -> FileNotFoundError
        with pytest.raises(FileNotFoundError) as excinfo:
            Image().load(str(tmp_path))
        assert str(tmp_path) in str(excinfo.value)

    def test_corrupt_file_raises(self, tmp_path):
        path = tmp_path / "broken.png"
        path.write_bytes(b"this is definitely not an image")
        with pytest.raises(ValueError) as excinfo:
            Image().load(str(path))
        assert str(path) in str(excinfo.value)

    def test_empty_file_raises(self, tmp_path):
        path = tmp_path / "empty.png"
        path.write_bytes(b"")
        with pytest.raises(ValueError) as excinfo:
            Image().load(str(path))
        assert str(path) in str(excinfo.value)

    def test_failed_load_keeps_previous_frame(self, sample_path, tmp_path):
        broken = tmp_path / "broken.png"
        broken.write_bytes(b"not an image either")
        image = Image()
        frame = image.load(str(sample_path))
        with pytest.raises(ValueError):
            image.load(str(broken))
        assert image.getFrame() is frame

    @pytest.mark.parametrize("path", ["", "   ", None])
    def test_invalid_path_raises(self, path):
        with pytest.raises(ValueError):
            Image().load(path)


class TestGetFrame:
    def test_none_before_load(self):
        assert Image().getFrame() is None

    def test_returns_loaded_frame(self, sample_path):
        image = Image()
        frame = image.load(str(sample_path))
        assert image.getFrame() is frame

    def test_consistent_across_calls(self, sample_path):
        image = Image()
        loaded = image.load(str(sample_path))
        assert np.array_equal(image.getFrame(), loaded)


class TestGetShape:
    def test_raises_before_load(self):
        with pytest.raises(ValueError):
            Image().getShape()

    def test_matches_frame(self, sample_path):
        image = Image()
        frame = image.load(str(sample_path))
        assert image.getShape() == frame.shape == (HEIGHT, WIDTH, 3)

    def test_agrees_with_get_frame(self, sample_path):
        image = Image()
        image.load(str(sample_path))
        height, width, channels = image.getShape()
        assert image.getFrame().shape == (height, width, channels)


class TestSetFrame:
    def test_holds_the_given_frame(self):
        frame = np.zeros((4, 6, 3), np.uint8)
        image = Image()
        image.setFrame(frame)
        assert image.getFrame() is frame
        assert image.getShape() == (4, 6, 3)

    def test_rejects_non_array(self):
        with pytest.raises(ValueError):
            Image().setFrame([[0, 0, 0]])
