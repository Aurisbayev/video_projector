"""Video support: VideoSource and PipelineClass.playVideo."""
import numpy as np
import pytest

import pipeline_class
from conftest import StubSetup
from image import Image
from pipeline_class import PipelineClass
from video_source import VideoSource

Q = ord("q")


def frameNumber(frame):
    """Which clip frame this is, read back from its grey value (the codec is lossy)."""
    return int(round((float(np.mean(frame)) - 10) / 20))


# ---- VideoSource ----

@pytest.mark.parametrize("path, expected", [
    ("a.mp4", True), ("A.MOV", True), ("x/y.avi", True), ("clip.mkv", True),
    ("a.jpg", False), ("a.png", False), ("a", False), ("", False), (None, False), (5, False),
])
def test_is_video_path(path, expected):
    assert VideoSource.isVideoPath(path) is expected


def test_reads_fps_count_and_shape(makeVideo):
    source = VideoSource(makeVideo(frames=6, fps=10.0, size=(64, 48)))
    assert source.getFps() == pytest.approx(10.0)
    assert source.getFrameCount() == 6
    assert source.getShape() == (48, 64, 3)
    source.close()


def test_missing_file_raises_and_names_it(tmp_path):
    with pytest.raises(FileNotFoundError, match="nope.avi"):
        VideoSource(str(tmp_path / "nope.avi"))


def test_file_that_is_not_a_video_raises(tmp_path):
    bad = tmp_path / "bad.avi"
    bad.write_text("this is not a video")
    with pytest.raises(ValueError, match="bad.avi"):
        VideoSource(str(bad))


@pytest.mark.parametrize("path", ["", "   ", None, 3])
def test_bad_path_raises(path):
    with pytest.raises(ValueError):
        VideoSource(path)


def test_frames_in_order_skip_and_seek_back(makeVideo):
    source = VideoSource(makeVideo(frames=6))
    assert [frameNumber(source.frameAt(i)) for i in (0, 1, 2)] == [0, 1, 2]
    assert frameNumber(source.frameAt(5)) == 5       # skips 3 and 4
    assert frameNumber(source.frameAt(1)) == 1       # seeks back
    assert frameNumber(source.frameAt(2)) == 2
    source.close()


def test_same_frame_twice_is_returned_again(makeVideo):
    source = VideoSource(makeVideo())
    first = source.frameAt(3)
    assert source.frameAt(3) is first
    assert frameNumber(source.frameAt(4)) == 4
    source.close()


@pytest.mark.parametrize("index", [-1, 6, 100, 1.5, "1", None])
def test_frame_index_out_of_range_raises(makeVideo, index):
    source = VideoSource(makeVideo(frames=6))
    with pytest.raises(ValueError):
        source.frameAt(index)
    source.close()


def test_closed_video_raises_and_close_is_repeatable(makeVideo):
    source = VideoSource(makeVideo())
    source.close()
    source.close()
    with pytest.raises(ValueError):
        source.frameAt(0)


# ---- PipelineClass ----

class ScriptedDisplay(object):
    """Stands in for Display. waitKey gives the keys in order and then keeps giving the last."""
    instances = []
    keys = []

    def __init__(self, *args, **kwargs):
        self.calls = []
        self.remaining = list(ScriptedDisplay.keys)
        ScriptedDisplay.instances.append(self)

    def show(self, frame):
        self.calls.append(("show", frame))

    def setFullscreen(self, enabled=True):
        self.calls.append(("setFullscreen", enabled))

    def waitKey(self, delayMs=0):
        self.calls.append(("waitKey", delayMs))
        return self.remaining.pop(0) if len(self.remaining) > 1 else self.remaining[0]

    def close(self):
        self.calls.append(("close",))

    def shown(self):
        return [c[1] for c in self.calls if c[0] == "show"]


@pytest.fixture
def scripted(monkeypatch):
    ScriptedDisplay.instances.clear()
    monkeypatch.setattr(pipeline_class, "Display", ScriptedDisplay)
    return ScriptedDisplay


def fakeClock(times):
    values = iter(times)
    return lambda: next(values)


def videoPipeline(makeSettings, makeVideo, side="LEFT", frames=6, fps=10.0, **kwargs):
    path = makeVideo(frames=frames, fps=fps, size=(80, 30))
    settings = makeSettings(side=side, resXY=(200, 60), d=80.0, sourcePath=path, **kwargs)
    from setup_class import SetupClass
    setup = SetupClass()
    setup.load(settings)
    assert setup.validate()
    return PipelineClass(setup)


def test_still_picture_is_not_a_video(makePipeline):
    assert makePipeline().isVideo() is False


def test_video_file_is_a_video(makeSettings, makeVideo):
    assert videoPipeline(makeSettings, makeVideo).isVideo() is True


def test_run_uses_playvideo_for_video_and_not_for_a_still(makeSettings, makeVideo, makePipeline, monkeypatch):
    calls = []
    monkeypatch.setattr(PipelineClass, "playVideo", lambda self, *a, **k: calls.append("video"))
    videoPipeline(makeSettings, makeVideo).run()
    assert calls == ["video"]


def test_waits_for_a_key_before_it_starts_the_clock(makeSettings, makeVideo, scripted):
    scripted.keys = [13, Q]          # Enter starts, q stops
    p = videoPipeline(makeSettings, makeVideo)
    ticks = []

    def clock():
        ticks.append(1)
        return 100.0

    p.playVideo(clock=clock)
    display = scripted.instances[0]
    names = [c[0] for c in display.calls]
    assert names[:4] == ["show", "setFullscreen", "waitKey", "show"]
    assert display.calls[2][1] == 0                  # the first wait has no time limit
    assert len(display.shown()) == 2                 # first picture, then one video frame
    assert len(ticks) == 2                           # start time, then one frame time


def test_quit_key_at_the_start_stops_before_playing(makeSettings, makeVideo, scripted):
    scripted.keys = [27]
    p = videoPipeline(makeSettings, makeVideo)
    p.playVideo(clock=fakeClock([]))                 # the clock must not be used
    display = scripted.instances[0]
    assert len(display.shown()) == 1
    assert display.calls[-1] == ("close",)


def test_frames_follow_the_clock_and_loop(makeSettings, makeVideo, scripted):
    # 6 frames at 10 fps: t = 0.0 -> 0, 0.25 -> 2, 0.45 -> 4, 0.65 -> 0 (loops), 1.15 -> 5
    scripted.keys = [13, -1, -1, -1, -1, Q]
    p = videoPipeline(makeSettings, makeVideo, frames=6, fps=10.0)
    p.playVideo(clock=fakeClock([5.0, 5.0, 5.25, 5.45, 5.65, 6.15]))
    shown = scripted.instances[0].shown()
    assert len(shown) == 1 + 5
    # The picture is a flat grey, so the mask shows as a brighter or darker strip only in
    # the overlap. The left part, outside the overlap, still carries the frame number.
    numbers = [frameNumber(f[:, :100]) for f in shown[1:]]
    assert numbers == [0, 2, 4, 0, 5]


def test_slow_computer_skips_frames_instead_of_falling_behind(makeSettings, makeVideo, scripted):
    scripted.keys = [13, -1, -1, Q]
    p = videoPipeline(makeSettings, makeVideo, frames=6, fps=10.0)
    p.playVideo(clock=fakeClock([0.0, 0.0, 0.1, 0.4]))
    numbers = [frameNumber(f[:, :100]) for f in scripted.instances[0].shown()[1:]]
    assert numbers == [0, 1, 4]


@pytest.mark.parametrize("side", ["LEFT", "RIGHT"])
def test_every_shown_frame_is_this_sides_masked_slice(makeSettings, makeVideo, scripted, side):
    scripted.keys = [13, Q]
    p = videoPipeline(makeSettings, makeVideo, side=side)
    p.playVideo(clock=fakeClock([0.0, 0.0]))
    for frame in scripted.instances[0].shown():
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (60, 200, 3) and frame.dtype == np.uint8


def test_overlap_columns_are_faded_and_the_rest_is_not(makeSettings, makeVideo, scripted):
    scripted.keys = [13, Q]
    p = videoPipeline(makeSettings, makeVideo, side="LEFT", gamma=1.0)
    p.playVideo(clock=fakeClock([0.0, 0.0]))
    shown = scripted.instances[0].shown()[0]
    overlap = 40                                        # resX 200, w 100, d 80
    outside = shown[:, :200 - overlap].astype(int)
    inside = shown[:, 200 - overlap:].astype(int)
    assert outside.max() - outside.min() <= 1           # flat grey outside the overlap
    assert inside[:, -1].mean() < inside[:, 0].mean()   # fades towards the right edge


def test_display_and_video_are_closed_when_playing_fails(makeSettings, makeVideo, scripted, monkeypatch):
    scripted.keys = [13, Q]
    p = videoPipeline(makeSettings, makeVideo)
    closed = []
    original = VideoSource.close
    monkeypatch.setattr(VideoSource, "close", lambda self: (closed.append(1), original(self)))
    monkeypatch.setattr(p, "scaleSource", lambda: (_ for _ in ()).throw(ValueError("boom")))
    with pytest.raises(ValueError, match="boom"):
        p.playVideo(clock=fakeClock([0.0]))
    assert scripted.instances[0].calls[-1] == ("close",)
    assert closed == [1]


def test_missing_video_file_raises(makeSettings, makeVideo, tmp_path):
    p = videoPipeline(makeSettings, makeVideo)
    (tmp_path / "clip.avi").unlink()
    with pytest.raises(FileNotFoundError, match="clip.avi"):
        p.playVideo()


def test_quit_keys_are_recognised():
    check = PipelineClass._PipelineClass__isQuitKey
    assert check(27) and check(Q) and check(0x100 | Q)
    assert not check(-1) and not check(ord("a"))
