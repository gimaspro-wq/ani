"""Tests for parser hardening helpers."""
from parser.utils import compute_diff, normalize_video_source
from parser.state import StateManager
from pathlib import Path


def test_compute_diff_detects_changes():
    old = {"a": 1, "b": 2}
    new = {"a": 1, "b": 3, "c": 4}
    diff = compute_diff(new, old)
    assert "b" in diff and diff["b"]["old"] == 2 and diff["b"]["new"] == 3
    assert "c" in diff and diff["c"]["old"] is None and diff["c"]["new"] == 4
    assert "a" not in diff


def test_normalize_video_source_filters_non_hls_and_empty():
    assert normalize_video_source("", "kodik", 0) is None
    assert normalize_video_source("http://example.com/video.mp4", "kodik", 0) is None
    payload = normalize_video_source("https://cdn.test/stream.m3u8", "kodik", 1)
    assert payload == {
        "type": "hls",
        "url": "https://cdn.test/stream.m3u8",
        "source_name": "kodik",
        "priority": 1,
    }


def test_state_manager_backwards_compatible_payload_fields(tmp_path: Path):
    state_file = tmp_path / "state.json"
    manager = StateManager(str(state_file))
    manager.mark_anime_processed(
        source_id="123",
        title="Test",
        episodes_count=2,
        anime_payload={"title": "Test"},
        episodes_payload={"123:1": {"source_episode_id": "123:1", "number": 1}},
        videos_payload={"url|kodik": {"url": "url", "source_name": "kodik", "type": "hls", "priority": 0}},
    )
    manager.save_state()

    # reload to ensure new fields are persisted and loadable
    reloaded = StateManager(str(state_file))
    entry = reloaded.get_anime_entry("123")
    assert entry["title"] == "Test"
    assert entry["episodes_count"] == 2
    assert entry["anime_payload"]["title"] == "Test"
    assert "123:1" in entry["episodes"]
    assert "url|kodik" in entry["videos"]
