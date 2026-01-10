"""Tests for video URL normalization utilities."""
from parser.utils import normalize_hls_url


def test_normalize_protocol_relative_kodik_link():
    """Protocol-relative Kodik link should be converted to https and m3u8."""
    url = "//kodik.info/video/123/abc/720p"
    assert normalize_hls_url(url) == "https://kodik.info/video/123/abc/720p.m3u8"


def test_normalize_preserves_existing_m3u8():
    """Existing m3u8 links remain unchanged."""
    url = "https://cdn.example.com/playlist.m3u8"
    assert normalize_hls_url(url) == url


def test_normalize_mp4_manifest():
    """MP4 links are converted to HLS manifest URLs."""
    url = "https://cdn.example.com/stream.mp4"
    assert normalize_hls_url(url) == "https://cdn.example.com/stream.mp4:hls:manifest.m3u8"


def test_normalize_empty_returns_none():
    """Empty or None returns None."""
    assert normalize_hls_url("") is None
    assert normalize_hls_url(None) is None
