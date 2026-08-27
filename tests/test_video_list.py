from ui.video_list import widget_key


def test_widget_keys_are_stable_by_mode_and_video_id():
    assert widget_key("machine", "video-42") == "machine-video-video-42"
    assert widget_key("manual", "video-42") == "manual-video-video-42"
    assert widget_key("machine", "video-42") != widget_key("manual", "video-42")
