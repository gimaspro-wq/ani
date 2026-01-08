"""Tests for anime internal and public APIs."""
import pytest
from fastapi.testclient import TestClient


class TestInternalAnimeAPI:
    """Tests for internal anime import API."""
    
    def test_import_anime_success(self, client: TestClient):
        """Test successful anime import."""
        data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime",
            "alternative_titles": ["テストアニメ"],
            "description": "Test anime description",
            "year": 2023,
            "status": "ongoing",
            "poster": "https://example.com/poster.jpg",
            "genres": ["Action", "Adventure"]
        }
        
        response = client.post(
            "/api/v1/internal/import/anime",
            json=data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "Test Anime" in result["message"]
    
    def test_import_anime_upsert(self, client: TestClient):
        """Test anime upsert - update existing anime."""
        data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime",
            "description": "Original description",
            "year": 2023,
            "status": "ongoing",
            "genres": ["Action"]
        }
        
        # First import
        response1 = client.post(
            "/api/v1/internal/import/anime",
            json=data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response1.status_code == 200
        
        # Update with new data
        data["description"] = "Updated description"
        data["genres"] = ["Action", "Adventure"]
        
        response2 = client.post(
            "/api/v1/internal/import/anime",
            json=data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response2.status_code == 200
        
        # Verify update via public API
        response3 = client.get("/api/v1/anime/test-anime")
        assert response3.status_code == 200
        anime = response3.json()
        assert anime["description"] == "Updated description"
        assert set(anime["genres"]) == {"Action", "Adventure"}
    
    def test_import_anime_invalid_token(self, client: TestClient):
        """Test anime import with invalid token."""
        data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime"
        }
        
        response = client.post(
            "/api/v1/internal/import/anime",
            json=data,
            headers={"X-Internal-Token": "invalid_token"}
        )
        
        assert response.status_code == 403
    
    def test_import_anime_missing_token(self, client: TestClient):
        """Test anime import without token."""
        data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime"
        }
        
        response = client.post("/api/v1/internal/import/anime", json=data)
        assert response.status_code == 422  # Missing required header
    
    def test_import_anime_invalid_status(self, client: TestClient):
        """Test anime import with invalid status."""
        data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime",
            "status": "invalid_status"
        }
        
        response = client.post(
            "/api/v1/internal/import/anime",
            json=data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 422
    
    def test_import_anime_slug_uniqueness(self, client: TestClient):
        """Test slug generation handles duplicates."""
        # Import first anime
        data1 = {
            "source_name": "source1",
            "source_id": "1",
            "title": "Test Anime"
        }
        response1 = client.post(
            "/api/v1/internal/import/anime",
            json=data1,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response1.status_code == 200
        
        # Import second anime with same title but different source
        data2 = {
            "source_name": "source2",
            "source_id": "2",
            "title": "Test Anime"
        }
        response2 = client.post(
            "/api/v1/internal/import/anime",
            json=data2,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response2.status_code == 200
        
        # Verify both are accessible with different slugs
        response3 = client.get("/api/v1/anime/test-anime")
        assert response3.status_code == 200
        
        response4 = client.get("/api/v1/anime/test-anime-1")
        assert response4.status_code == 200


class TestInternalEpisodesAPI:
    """Tests for internal episodes import API."""
    
    def test_import_episodes_success(self, client: TestClient):
        """Test successful episodes import."""
        # First create anime
        anime_data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime"
        }
        client.post(
            "/api/v1/internal/import/anime",
            json=anime_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # Import episodes
        episodes_data = {
            "source_name": "test_source",
            "anime_source_id": "12345",
            "episodes": [
                {
                    "source_episode_id": "ep_1",
                    "number": 1,
                    "title": "Episode 1",
                    "is_available": True
                },
                {
                    "source_episode_id": "ep_2",
                    "number": 2,
                    "title": "Episode 2",
                    "is_available": True
                }
            ]
        }
        
        response = client.post(
            "/api/v1/internal/import/episodes",
            json=episodes_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["total"] == 2
        assert result["imported"] == 2
        assert len(result["errors"]) == 0
    
    def test_import_episodes_upsert(self, client: TestClient):
        """Test episodes upsert - update existing episodes."""
        # Create anime
        anime_data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime"
        }
        client.post(
            "/api/v1/internal/import/anime",
            json=anime_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # First import
        episodes_data = {
            "source_name": "test_source",
            "anime_source_id": "12345",
            "episodes": [
                {
                    "source_episode_id": "ep_1",
                    "number": 1,
                    "title": "Episode 1",
                    "is_available": True
                }
            ]
        }
        response1 = client.post(
            "/api/v1/internal/import/episodes",
            json=episodes_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response1.status_code == 200
        
        # Update episode title
        episodes_data["episodes"][0]["title"] = "Updated Episode 1"
        response2 = client.post(
            "/api/v1/internal/import/episodes",
            json=episodes_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response2.status_code == 200
        
        # Verify via public API
        response3 = client.get("/api/v1/anime/test-anime/episodes")
        assert response3.status_code == 200
        episodes = response3.json()
        assert len(episodes) == 1
        assert episodes[0]["title"] == "Updated Episode 1"
    
    def test_import_episodes_anime_not_found(self, client: TestClient):
        """Test episodes import for non-existent anime."""
        episodes_data = {
            "source_name": "test_source",
            "anime_source_id": "nonexistent",
            "episodes": [
                {
                    "source_episode_id": "ep_1",
                    "number": 1,
                    "title": "Episode 1",
                    "is_available": True
                }
            ]
        }
        
        response = client.post(
            "/api/v1/internal/import/episodes",
            json=episodes_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 404
    
    def test_import_episodes_partial_errors(self, client: TestClient):
        """Test episodes import handles partial errors."""
        # Create anime
        anime_data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime"
        }
        client.post(
            "/api/v1/internal/import/anime",
            json=anime_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # Import episodes with some valid and some invalid
        episodes_data = {
            "source_name": "test_source",
            "anime_source_id": "12345",
            "episodes": [
                {
                    "source_episode_id": "ep_1",
                    "number": 1,
                    "title": "Episode 1",
                    "is_available": True
                }
            ]
        }
        
        response = client.post(
            "/api/v1/internal/import/episodes",
            json=episodes_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 1
        assert result["imported"] >= 0


class TestInternalVideoAPI:
    """Tests for internal video source import API."""
    
    def test_import_video_success(self, client: TestClient):
        """Test successful video source import."""
        # Create anime
        anime_data = {
            "source_name": "test_source",
            "source_id": "12345",
            "title": "Test Anime"
        }
        client.post(
            "/api/v1/internal/import/anime",
            json=anime_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # Create episode
        episodes_data = {
            "source_name": "test_source",
            "anime_source_id": "12345",
            "episodes": [
                {
                    "source_episode_id": "ep_1",
                    "number": 1,
                    "title": "Episode 1",
                    "is_available": True
                }
            ]
        }
        client.post(
            "/api/v1/internal/import/episodes",
            json=episodes_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # Import video source
        video_data = {
            "source_name": "test_source",
            "source_episode_id": "ep_1",
            "player": {
                "type": "iframe",
                "url": "https://player.example.com/embed/abc",
                "source_name": "example_player",
                "priority": 1
            }
        }
        
        response = client.post(
            "/api/v1/internal/import/video",
            json=video_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_import_video_multiple_sources(self, client: TestClient):
        """Test importing multiple video sources for one episode."""
        # Setup anime and episode
        client.post(
            "/api/v1/internal/import/anime",
            json={
                "source_name": "test_source",
                "source_id": "12345",
                "title": "Test Anime"
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        client.post(
            "/api/v1/internal/import/episodes",
            json={
                "source_name": "test_source",
                "anime_source_id": "12345",
                "episodes": [
                    {
                        "source_episode_id": "ep_1",
                        "number": 1,
                        "title": "Episode 1",
                        "is_available": True
                    }
                ]
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # Import first video source
        video_data1 = {
            "source_name": "test_source",
            "source_episode_id": "ep_1",
            "player": {
                "type": "iframe",
                "url": "https://player1.example.com/embed/abc",
                "source_name": "player1",
                "priority": 1
            }
        }
        response1 = client.post(
            "/api/v1/internal/import/video",
            json=video_data1,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response1.status_code == 200
        
        # Import second video source
        video_data2 = {
            "source_name": "test_source",
            "source_episode_id": "ep_1",
            "player": {
                "type": "iframe",
                "url": "https://player2.example.com/embed/xyz",
                "source_name": "player2",
                "priority": 2
            }
        }
        response2 = client.post(
            "/api/v1/internal/import/video",
            json=video_data2,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        assert response2.status_code == 200
        
        # Verify via public API - should be sorted by priority
        response3 = client.get("/api/v1/anime/test-anime/episodes")
        assert response3.status_code == 200
        episodes = response3.json()
        assert len(episodes) == 1
        assert len(episodes[0]["video_sources"]) == 2
        # Higher priority first
        assert episodes[0]["video_sources"][0]["priority"] == 2
        assert episodes[0]["video_sources"][1]["priority"] == 1
    
    def test_import_video_episode_not_found(self, client: TestClient):
        """Test video import for non-existent episode."""
        video_data = {
            "source_name": "test_source",
            "source_episode_id": "nonexistent",
            "player": {
                "type": "iframe",
                "url": "https://player.example.com/embed/abc",
                "source_name": "example_player",
                "priority": 1
            }
        }
        
        response = client.post(
            "/api/v1/internal/import/video",
            json=video_data,
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        assert response.status_code == 404


class TestPublicAnimeAPI:
    """Tests for public anime API."""
    
    def test_list_anime_empty(self, client: TestClient):
        """Test listing anime when none exist."""
        response = client.get("/api/v1/anime")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_anime_with_data(self, client: TestClient):
        """Test listing anime."""
        # Create test anime
        for i in range(3):
            client.post(
                "/api/v1/internal/import/anime",
                json={
                    "source_name": "test_source",
                    "source_id": f"anime_{i}",
                    "title": f"Test Anime {i}",
                    "year": 2023 + i,
                    "genres": ["Action"]
                },
                headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
            )
        
        response = client.get("/api/v1/anime")
        assert response.status_code == 200
        anime_list = response.json()
        assert len(anime_list) == 3
        assert all("source_id" not in a for a in anime_list)  # Internal fields hidden
    
    def test_list_anime_pagination(self, client: TestClient):
        """Test anime list pagination."""
        # Create 5 anime
        for i in range(5):
            client.post(
                "/api/v1/internal/import/anime",
                json={
                    "source_name": "test_source",
                    "source_id": f"anime_{i}",
                    "title": f"Test Anime {i}"
                },
                headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
            )
        
        # Get first page
        response1 = client.get("/api/v1/anime?skip=0&limit=2")
        assert response1.status_code == 200
        page1 = response1.json()
        assert len(page1) == 2
        
        # Get second page
        response2 = client.get("/api/v1/anime?skip=2&limit=2")
        assert response2.status_code == 200
        page2 = response2.json()
        assert len(page2) == 2
    
    def test_list_anime_filter_by_year(self, client: TestClient):
        """Test filtering anime by year."""
        client.post(
            "/api/v1/internal/import/anime",
            json={
                "source_name": "test_source",
                "source_id": "anime_1",
                "title": "Anime 2023",
                "year": 2023
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        client.post(
            "/api/v1/internal/import/anime",
            json={
                "source_name": "test_source",
                "source_id": "anime_2",
                "title": "Anime 2024",
                "year": 2024
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        response = client.get("/api/v1/anime?year=2023")
        assert response.status_code == 200
        anime_list = response.json()
        assert len(anime_list) == 1
        assert anime_list[0]["year"] == 2023
    
    def test_get_anime_by_slug(self, client: TestClient):
        """Test getting anime by slug."""
        client.post(
            "/api/v1/internal/import/anime",
            json={
                "source_name": "test_source",
                "source_id": "12345",
                "title": "Test Anime",
                "description": "Test description",
                "year": 2023,
                "status": "ongoing",
                "genres": ["Action", "Adventure"],
                "alternative_titles": ["テストアニメ"]
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        response = client.get("/api/v1/anime/test-anime")
        assert response.status_code == 200
        anime = response.json()
        assert anime["title"] == "Test Anime"
        assert anime["slug"] == "test-anime"
        assert anime["description"] == "Test description"
        assert anime["year"] == 2023
        assert anime["status"] == "ongoing"
        assert set(anime["genres"]) == {"Action", "Adventure"}
        assert "source_id" not in anime  # Internal field hidden
    
    def test_get_anime_not_found(self, client: TestClient):
        """Test getting non-existent anime."""
        response = client.get("/api/v1/anime/nonexistent")
        assert response.status_code == 404
    
    def test_get_anime_episodes(self, client: TestClient):
        """Test getting anime episodes with video sources."""
        # Setup anime, episodes, and video sources
        client.post(
            "/api/v1/internal/import/anime",
            json={
                "source_name": "test_source",
                "source_id": "12345",
                "title": "Test Anime"
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        client.post(
            "/api/v1/internal/import/episodes",
            json={
                "source_name": "test_source",
                "anime_source_id": "12345",
                "episodes": [
                    {
                        "source_episode_id": "ep_1",
                        "number": 1,
                        "title": "Episode 1",
                        "is_available": True
                    },
                    {
                        "source_episode_id": "ep_2",
                        "number": 2,
                        "title": "Episode 2",
                        "is_available": True
                    }
                ]
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        # Add video sources with different priorities
        client.post(
            "/api/v1/internal/import/video",
            json={
                "source_name": "test_source",
                "source_episode_id": "ep_1",
                "player": {
                    "type": "iframe",
                    "url": "https://player1.example.com/embed/abc",
                    "source_name": "player1",
                    "priority": 1
                }
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        client.post(
            "/api/v1/internal/import/video",
            json={
                "source_name": "test_source",
                "source_episode_id": "ep_1",
                "player": {
                    "type": "iframe",
                    "url": "https://player2.example.com/embed/xyz",
                    "source_name": "player2",
                    "priority": 10
                }
            },
            headers={"X-Internal-Token": "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS"}
        )
        
        response = client.get("/api/v1/anime/test-anime/episodes")
        assert response.status_code == 200
        episodes = response.json()
        assert len(episodes) == 2
        assert episodes[0]["number"] == 1
        assert episodes[1]["number"] == 2
        
        # Check video sources are sorted by priority (descending)
        assert len(episodes[0]["video_sources"]) == 2
        assert episodes[0]["video_sources"][0]["priority"] == 10
        assert episodes[0]["video_sources"][1]["priority"] == 1
        
        # Check internal fields are hidden
        assert "source_episode_id" not in episodes[0]
    
    def test_get_episodes_anime_not_found(self, client: TestClient):
        """Test getting episodes for non-existent anime."""
        response = client.get("/api/v1/anime/nonexistent/episodes")
        assert response.status_code == 404
