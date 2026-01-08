"""Test configuration for parser tests."""
import pytest


@pytest.fixture
def sample_shikimori_data():
    """Sample Shikimori API response."""
    return {
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
        },
        "genres": [
            {"id": 1, "name": "Action"},
        ],
    }


@pytest.fixture
def sample_kodik_data():
    """Sample Kodik API response."""
    return {
        "total": 1,
        "results": [
            {
                "id": "test-id",
                "title": "Test Anime",
                "material_data": {
                    "shikimori_id": "12345",
                },
                "link": "https://kodik.cc/seria/12345/hash",
                "translation": {
                    "id": 1,
                    "title": "Test Translation",
                },
                "seasons": {
                    "1": {
                        "1": {"title": "Episode 1"},
                        "2": {"title": "Episode 2"},
                    }
                },
            }
        ],
    }
