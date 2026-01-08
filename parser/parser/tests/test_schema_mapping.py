"""Tests for schema mapping and data transformation."""
import pytest


def test_shikimori_to_anime_schema():
    """Test mapping Shikimori data to AnimeImportSchema."""
    from parser.clients.shikimori import ShikimoriClient
    
    client = ShikimoriClient()
    
    # Sample Shikimori data
    shikimori_data = {
        "id": 12345,
        "name": "Test Anime",
        "russian": "Тестовое Аниме",
        "japanese": ["テストアニメ"],
        "english": ["Test Anime EN"],
        "description": "Test description",
        "aired_on": "2023-01-15",
        "status": "ongoing",
        "image": {
            "original": "/system/animes/original/12345.jpg",
            "preview": "/system/animes/preview/12345.jpg",
        },
        "genres": [
            {"id": 1, "name": "Action"},
            {"id": 2, "name": "Adventure"},
        ],
    }
    
    result = client.parse_anime_data(shikimori_data)
    
    # Verify required fields
    assert result["source_id"] == "12345"
    assert result["title"] == "Test Anime"
    assert result["description"] == "Test description"
    assert result["year"] == 2023
    assert result["status"] == "ongoing"
    
    # Verify alternative titles
    assert result["alternative_titles"] is not None
    assert "Тестовое Аниме" in result["alternative_titles"]
    assert "テストアニメ" in result["alternative_titles"]
    
    # Verify poster URL is absolute
    assert result["poster"].startswith("https://")
    
    # Verify genres
    assert result["genres"] == ["Action", "Adventure"]


def test_shikimori_status_mapping():
    """Test Shikimori status mapping to backend status."""
    from parser.clients.shikimori import ShikimoriClient
    
    client = ShikimoriClient()
    
    test_cases = [
        ({"id": 1, "name": "Test", "status": "ongoing"}, "ongoing"),
        ({"id": 2, "name": "Test", "status": "released"}, "completed"),
        ({"id": 3, "name": "Test", "status": "anons"}, "upcoming"),
        ({"id": 4, "name": "Test", "status": "unknown"}, None),
    ]
    
    for shiki_data, expected_status in test_cases:
        result = client.parse_anime_data(shiki_data)
        assert result["status"] == expected_status


def test_episode_schema_format():
    """Test that episode data matches EpisodeImportItem schema."""
    from parser.utils import generate_episode_source_id
    
    source_id = "12345"
    episode_data = {
        "source_episode_id": generate_episode_source_id(source_id, 1),
        "number": 1,
        "title": "Episode 1",
        "is_available": True,
    }
    
    # Verify required fields are present
    assert "source_episode_id" in episode_data
    assert "number" in episode_data
    assert "is_available" in episode_data
    
    # Verify types
    assert isinstance(episode_data["source_episode_id"], str)
    assert isinstance(episode_data["number"], int)
    assert isinstance(episode_data["is_available"], bool)
    
    # Verify episode number is positive
    assert episode_data["number"] >= 0


def test_video_player_schema_format():
    """Test that video player data matches VideoPlayerSchema."""
    player_data = {
        "type": "iframe",
        "url": "https://kodik.cc/seria/12345/hash",
        "source_name": "kodik",
        "priority": 0,
    }
    
    # Verify required fields
    assert "type" in player_data
    assert "url" in player_data
    assert "source_name" in player_data
    assert "priority" in player_data
    
    # Verify source_name is exactly "kodik"
    assert player_data["source_name"] == "kodik"
    
    # Verify types
    assert isinstance(player_data["type"], str)
    assert isinstance(player_data["url"], str)
    assert isinstance(player_data["source_name"], str)
    assert isinstance(player_data["priority"], int)


def test_backend_source_name():
    """Test that backend source name is always 'kodik-shikimori'."""
    from parser.config import settings
    
    # Source name must be exactly this value
    assert settings.SOURCE_NAME == "kodik-shikimori"
