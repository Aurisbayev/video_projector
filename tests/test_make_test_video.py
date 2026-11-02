"""tools/make_test_video.py tests."""
import os
import sys

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import make_test_video


def test_writes_a_readable_video(tmp_path):
    out = tmp_path / "t.mp4"
    assert make_test_video.main([str(out), "--seconds", "1", "--fps", "10", "--size", "320x100"]) == 0
    capture = cv2.VideoCapture(str(out))
    assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 10
    assert int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 320
    capture.release()


def test_bad_size_exits_1(tmp_path, capsys):
    assert make_test_video.main([str(tmp_path / "t.mp4"), "--size", "big"]) == 1
    assert "--size" in capsys.readouterr().err
