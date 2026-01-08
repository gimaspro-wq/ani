import httpx

from parser.client import HttpClient
from parser.config import Settings
from parser.source_adapters import GogoAnimeAdapter


def test_gogoanime_adapter_parses_flow():
    base_url = "https://api.consumet.org/anime/gogoanime"

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/top-airing"):
            return httpx.Response(
                200,
                json={
                    "hasNextPage": False,
                    "results": [
                        {
                            "id": "demo-anime",
                            "title": "Demo Anime",
                            "image": "https://img/cdn.jpg",
                            "releaseDate": "2024",
                            "status": "Ongoing",
                            "genres": ["Action", "Comedy"],
                        }
                    ],
                },
            )
        if "/info/" in path:
            return httpx.Response(
                200,
                json={
                    "description": "Some description",
                    "status": "Ongoing",
                    "genres": ["Action", "Comedy"],
                    "image": "https://img/cdn.jpg",
                    "releaseDate": "2024",
                    "episodes": [
                        {"id": "demo-anime-episode-1", "number": 1, "title": "Episode 1"},
                        {"id": "demo-anime-episode-2", "number": 2},
                    ],
                },
            )
        if "/watch/" in path:
            return httpx.Response(
                200,
                json={
                    "sources": [
                        {"url": "https://cdn/video-720.mp4", "isM3U8": False, "quality": "720p", "server": "cdn-1"},
                        {"url": "https://cdn/video.m3u8", "isM3U8": True, "quality": "1080p", "server": "hls-1"},
                    ]
                },
            )
        return httpx.Response(404)

    settings = Settings()
    settings.consumet_base_url = base_url
    client = HttpClient(
        timeout=5,
        max_retries=1,
        backoff_factor=0,
        rate_limit_per_second=100,
        transport=httpx.MockTransport(handler),
    )

    adapter = GogoAnimeAdapter(client, settings)
    anime_list = list(adapter.fetch_anime_list(limit=1))
    assert len(anime_list) == 1
    anime = anime_list[0]
    assert anime.source_id == "demo-anime"
    assert anime.status == "ongoing"
    assert anime.year == 2024

    episodes = adapter.fetch_episodes(anime)
    assert len(episodes) == 2
    assert episodes[0].source_episode_id == "demo-anime-episode-1"
    assert episodes[0].number == 1

    video = adapter.fetch_video(episodes[0])
    assert video is not None
    assert video.player.type == "m3u8"
    assert video.player.url.endswith(".m3u8")
