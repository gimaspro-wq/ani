"""Tests for ID generation logic."""
import pytest
from parser.utils import generate_source_id, generate_episode_source_id


def test_generate_source_id():
    """Test source_id generation from Shikimori ID."""
    assert generate_source_id(12345) == "12345"
    assert generate_source_id(1) == "1"
    assert generate_source_id(999999) == "999999"


def test_generate_episode_source_id():
    """Test episode source_id generation."""
    assert generate_episode_source_id("12345", 1) == "12345:1"
    assert generate_episode_source_id("12345", 100) == "12345:100"
    assert generate_episode_source_id("999", 5) == "999:5"


def test_id_determinism():
    """Test that ID generation is deterministic."""
    # Same input should always produce same output
    shiki_id = 12345
    ep_num = 1
    
    source_id_1 = generate_source_id(shiki_id)
    source_id_2 = generate_source_id(shiki_id)
    assert source_id_1 == source_id_2
    
    ep_id_1 = generate_episode_source_id(source_id_1, ep_num)
    ep_id_2 = generate_episode_source_id(source_id_1, ep_num)
    assert ep_id_1 == ep_id_2


def test_episode_id_format():
    """Test that episode IDs follow the required format."""
    source_id = "12345"
    episode_number = 42
    
    ep_id = generate_episode_source_id(source_id, episode_number)
    
    # Should contain colon separator
    assert ":" in ep_id
    
    # Should be parseable back to components
    parts = ep_id.split(":")
    assert len(parts) == 2
    assert parts[0] == source_id
    assert parts[1] == str(episode_number)
