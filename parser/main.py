import argparse
import logging
import sys
from typing import Iterable

from parser.client import BackendClient, HttpClient
from parser.config import Settings, load_settings
from parser.normalizer import Anime, Episode, VideoSource
from parser.source_adapters import GogoAnimeAdapter


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def process_anime(
    backend: BackendClient,
    adapter: GogoAnimeAdapter,
    anime_items: Iterable[Anime],
) -> None:
    for anime in anime_items:
        try:
            if not backend.import_anime(anime):
                continue
            episodes = adapter.fetch_episodes(anime)
            if not episodes:
                continue
            backend.import_episodes(adapter.source_name, anime.source_id, episodes)
            for episode in episodes:
                video = adapter.fetch_video(episode)
                if video:
                    backend.import_video(video)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to process anime %s: %s", anime.title, exc)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Anime parser for gogoanime via consumet API.")
    parser.add_argument("--limit", type=int, default=None, help="Number of anime items to import.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    parser.add_argument("--dry-run", action="store_true", help="Skip backend writes.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    settings = load_settings()
    if args.limit is not None:
        settings.source_limit = args.limit
    if args.dry_run:
        settings.dry_run = True

    configure_logging(args.verbose)
    logging.info("Starting parser with limit=%s dry_run=%s", settings.source_limit, settings.dry_run)

    http_client = HttpClient(
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
        backoff_factor=settings.backoff_factor,
        rate_limit_per_second=settings.rate_limit_per_second,
        user_agents=settings.user_agents,
    )
    adapter = GogoAnimeAdapter(http_client, settings)
    backend = BackendClient(settings.backend_url, settings.internal_token, http_client, dry_run=settings.dry_run)

    try:
        anime_iter = adapter.fetch_anime_list(settings.source_limit)
        process_anime(backend, adapter, anime_iter)
    finally:
        http_client.close()
    logging.info("Parser run completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
